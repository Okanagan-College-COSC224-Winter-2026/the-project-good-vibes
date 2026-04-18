"""
User management endpoints
"""

import os

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, set_access_cookies
from marshmallow import Schema, ValidationError, fields, validate
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename

from ..models import User, UserSchema

bp = Blueprint("user", __name__, url_prefix="/user")

# Create schema instances once (reusable)
user_schema = UserSchema()

ALLOWED_AVATAR_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}


def _allowed_avatar(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_AVATAR_EXTENSIONS


class UserUpdateSchema(Schema):
    """Schema for updating user information"""

    name = fields.Str(validate=validate.Length(min=1, max=255))
    email = fields.Email()


user_update_schema = UserUpdateSchema()


@bp.route("/", methods=["GET"])
@jwt_required()
def get_current_user():
    """Get current authenticated user information"""
    email = get_jwt_identity()
    user = User.get_by_email(email)

    if not user:
        return jsonify({"msg": "User not found"}), 404
    return jsonify(user_schema.dump(user)), 200


@bp.route("/<int:user_id>", methods=["GET"])
@jwt_required()
def get_user_by_id(user_id):
    """Get user by ID (users can view their own info, teachers/admins can view anyone)"""
    current_email = get_jwt_identity()
    current_user = User.get_by_email(current_email)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Users can view their own info, teachers and admins can view anyone
    if current_user.id != user_id and not current_user.has_role("teacher", "admin"):
        return jsonify({"msg": "Insufficient permissions"}), 403

    return jsonify(user_schema.dump(user)), 200


@bp.route("/", methods=["PUT"])
@jwt_required()
def update_current_user():
    """Update current user's name and/or email"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    try:
        data = user_update_schema.load(request.json)
    except ValidationError as err:
        return jsonify({"msg": "Validation error", "errors": err.messages}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if "name" in data:
        user.name = data["name"]

    email_changed = False
    if "email" in data and data["email"] != user.email:
        # Ensure new email is not already taken by another user
        existing = User.get_by_email(data["email"])
        if existing and existing.id != user.id:
            return jsonify({"msg": "Email address is already in use"}), 400
        user.email = data["email"]
        email_changed = True

    user.update()

    response_data = user_schema.dump(user)

    if email_changed:
        # Reissue JWT with updated email so the session remains valid
        response = jsonify(response_data)
        new_token = create_access_token(identity=user.email)
        set_access_cookies(response, new_token)
        return response, 200

    return jsonify(response_data), 200


@bp.route("/avatar", methods=["POST"])
@jwt_required()
def upload_avatar():
    """Upload or replace the current user's avatar image"""
    if "avatar" not in request.files:
        return jsonify({"msg": "No avatar file provided"}), 400

    file = request.files["avatar"]
    if not file or not file.filename:
        return jsonify({"msg": "No file selected"}), 400

    if not _allowed_avatar(file.filename):
        allowed = ", ".join(sorted(ALLOWED_AVATAR_EXTENSIONS))
        return jsonify({"msg": f"File type not allowed. Allowed types: {allowed}"}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    ext = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"user_{user.id}.{ext}")

    avatars_dir = os.path.join(current_app.instance_path, "uploads", "avatars")
    os.makedirs(avatars_dir, exist_ok=True)

    # Remove previous avatar file if extension changed
    if user.avatar_path and user.avatar_path != filename:
        old_path = os.path.join(avatars_dir, user.avatar_path)
        if os.path.exists(old_path):
            os.remove(old_path)

    file.save(os.path.join(avatars_dir, filename))
    user.avatar_path = filename
    user.update()

    return jsonify(user_schema.dump(user)), 200


@bp.route("/avatar/<int:user_id>", methods=["GET"])
@jwt_required()
def get_avatar(user_id):
    """Serve the avatar image for a user"""
    user = User.get_by_id(user_id)
    if not user or not user.avatar_path:
        return jsonify({"msg": "No avatar found"}), 404

    avatars_dir = os.path.join(current_app.instance_path, "uploads", "avatars")
    return send_from_directory(avatars_dir, user.avatar_path)


@bp.route("/<int:user_id>", methods=["DELETE"])
@jwt_required()
def delete_user(user_id):
    """Delete user (admin only or own account)"""
    current_email = get_jwt_identity()
    current_user = User.get_by_email(current_email)

    if not current_user:
        return jsonify({"msg": "User not found"}), 404

    user = User.get_by_id(user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Users can delete their own account, admins can delete anyone
    if current_user.id != user_id and not current_user.is_admin():
        return jsonify({"msg": "Insufficient permissions"}), 403

    user.delete()

    return jsonify({"msg": "User deleted successfully"}), 200


@bp.route("/password", methods=["PATCH"])
@jwt_required()
def change_password():
    """Change current user's password (only if must_change_password is True)"""
    if not request.is_json:
        return jsonify({"msg": "Missing JSON in request"}), 400

    current_password = request.json.get("current_password", None)
    new_password = request.json.get("new_password", None)

    if not current_password:
        return jsonify({"msg": "Current password is required"}), 400
    if not new_password:
        return jsonify({"msg": "New password is required"}), 400
    if len(new_password) < 6:
        return jsonify({"msg": "New password must be at least 6 characters"}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Security: Only allow password changes if must_change_password is True
    if not user.must_change_password:
        return jsonify({"msg": "Password change not required for this account"}), 403

    # Verify current password
    if not check_password_hash(user.hash_pass, current_password):
        return jsonify({"msg": "Current password is incorrect"}), 401

    # Update password and clear must_change_password flag
    user.hash_pass = generate_password_hash(new_password)
    user.must_change_password = False
    user.update()

    return jsonify({"msg": "Password updated successfully"}), 200
