from pathlib import Path
import os
import secrets

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from ..models import Assignment, AssignmentResource, Course, User, User_Course
from .auth_controller import jwt_role_required, jwt_teacher_required

bp = Blueprint("assignment_resource", __name__, url_prefix="/assignment-resource")

ALLOWED_EXTENSIONS = {
    "txt",
    "pdf",
    "doc",
    "docx",
    "ppt",
    "pptx",
    "xls",
    "xlsx",
    "csv",
    "zip",
    "png",
    "jpg",
    "jpeg",
}
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024


def _get_current_user() -> User | None:
    email = get_jwt_identity()
    if not email:
        return None
    return User.get_by_email(email)


def _can_access_course(user: User, course: Course):
    if user.is_admin():
        return True
    if user.is_teacher() and course.teacherID == user.id:
        return True
    if user.is_student() and User_Course.get(user.id, course.id):
        return True
    return False


def _uploads_root() -> str:
    root = os.path.join(current_app.instance_path, "uploads", "assignment_resources")
    os.makedirs(root, exist_ok=True)
    return root


def _is_allowed_filename(filename: str) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def _resource_payload(resource: AssignmentResource):
    return {
        "id": resource.id,
        "assignmentID": resource.assignmentID,
        "uploaderID": resource.uploaderID,
        "original_name": resource.original_name,
        "download_url": f"/assignment-resource/file/{resource.id}",
        "created_at": resource.created_at.isoformat() if resource.created_at else None,
    }


@bp.route("/assignment/<int:assignment_id>", methods=["GET"])
@jwt_role_required("student", "teacher", "admin")
def list_assignment_resources(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not _can_access_course(user, course):
        return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    resources = AssignmentResource.get_for_assignment(assignment_id)
    return jsonify({"resources": [_resource_payload(resource) for resource in resources]}), 200


@bp.route("/assignment/<int:assignment_id>", methods=["POST"])
@jwt_teacher_required
def upload_assignment_resource(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not user.is_admin() and course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"msg": "No file provided"}), 400

    original_name = secure_filename(upload.filename)
    if not original_name:
        return jsonify({"msg": "Invalid file name"}), 400

    if not _is_allowed_filename(original_name):
        return jsonify({"msg": "Unsupported file type"}), 400

    upload.seek(0, os.SEEK_END)
    file_size = upload.tell()
    upload.seek(0)
    if file_size > MAX_FILE_SIZE_BYTES:
        return jsonify({"msg": "File is too large (max 20MB)"}), 400

    assignment_dir = os.path.join(_uploads_root(), f"assignment_{assignment_id}")
    os.makedirs(assignment_dir, exist_ok=True)

    random_suffix = secrets.token_hex(8)
    stored_name = f"teacher_{user.id}_{random_suffix}_{original_name}"
    stored_path = os.path.join(assignment_dir, stored_name)
    upload.save(stored_path)

    resource = AssignmentResource(
        assignmentID=assignment_id,
        uploaderID=user.id,
        original_name=original_name,
        path=stored_path,
    )
    AssignmentResource.create(resource)

    return jsonify({"msg": "Resource uploaded", "resource": _resource_payload(resource)}), 201


@bp.route("/<int:resource_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_assignment_resource(resource_id):
    resource = AssignmentResource.get_by_id(resource_id)
    if not resource:
        return jsonify({"msg": "Resource not found"}), 404

    assignment = Assignment.get_by_id(resource.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not user.is_admin() and course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    file_path = resource.path
    resource.delete()
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass

    return jsonify({"msg": "Resource deleted"}), 200


@bp.route("/file/<int:resource_id>", methods=["GET"])
@jwt_role_required("student", "teacher", "admin")
def download_assignment_resource(resource_id):
    resource = AssignmentResource.get_by_id(resource_id)
    if not resource:
        return jsonify({"msg": "Resource not found"}), 404

    assignment = Assignment.get_by_id(resource.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not _can_access_course(user, course):
        return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    file_path = Path(resource.path)
    if not file_path.exists():
        return jsonify({"msg": "Resource file is missing"}), 404

    return send_from_directory(file_path.parent, file_path.name, as_attachment=True)