from pathlib import Path
import os
import secrets

from flask import Blueprint, current_app, jsonify, request, send_from_directory
from flask_jwt_extended import get_jwt_identity
from werkzeug.utils import secure_filename

from ..models import Assignment, CourseGroup, Group_Members, Submission, User, User_Course, db
from .auth_controller import jwt_role_required

bp = Blueprint("submission", __name__, url_prefix="/submission")

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


def _uploads_root() -> str:
    root = os.path.join(current_app.instance_path, "uploads")
    os.makedirs(root, exist_ok=True)
    return root


def _delete_file_if_exists(file_path: str | None) -> None:
    if file_path and os.path.exists(file_path):
        try:
            os.remove(file_path)
        except OSError:
            pass


def _is_allowed_filename(filename: str) -> bool:
    if "." not in filename:
        return False
    extension = filename.rsplit(".", 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS


def _attachment_payload(submission: Submission):
    if not submission.path:
        return None

    return {
        "id": submission.id,
        "filename": os.path.basename(submission.path),
        "download_url": f"/submission/file/{submission.id}",
        "studentID": submission.studentID,
        "assignmentID": submission.assignmentID,
    }


def _get_current_user() -> User | None:
    email = get_jwt_identity()
    if not email:
        return None
    return User.get_by_email(email)


def _ensure_student_enrolled_for_assignment(user: User, assignment: Assignment):
    if not user.is_student():
        return False
    return User_Course.get(user.id, assignment.courseID) is not None


def _get_group_submission(user_id: int, assignment: Assignment):
    """Return a group member's submission for this assignment, or None.

    Looks up the user's group in the assignment's course and returns the first
    submission found from any member of that group.
    """
    membership = (
        Group_Members.query
        .join(CourseGroup, CourseGroup.id == Group_Members.groupID)
        .filter(Group_Members.userID == user_id, CourseGroup.courseID == assignment.courseID)
        .first()
    )
    if not membership:
        return None

    group_member_ids = [
        m.userID for m in Group_Members.query.filter_by(groupID=membership.groupID).all()
    ]
    return Submission.query.filter(
        Submission.assignmentID == assignment.id,
        Submission.studentID.in_(group_member_ids),
    ).first()


@bp.route("/<int:assignment_id>/student/<int:student_id>", methods=["GET"])
@jwt_role_required("student", "teacher", "admin")
def get_student_submission(assignment_id, student_id):
    """View another user's submission for an assignment.

    Teachers/admins: always allowed.
    Students: must be enrolled in the course.
    """
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Students must be enrolled in the course
    if user.is_student():
        if not User_Course.get(user.id, assignment.courseID):
            return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    # Look up the target student's submission (or their group's)
    target = User.get_by_id(student_id)
    if not target:
        return jsonify({"msg": "Student not found"}), 404

    submission = Submission.query.filter_by(
        assignmentID=assignment_id, studentID=student_id
    ).first()

    if not submission:
        submission = _get_group_submission(student_id, assignment)

    return jsonify({"submission": _attachment_payload(submission) if submission else None}), 200


@bp.route("/<int:assignment_id>/mine", methods=["GET"])
@jwt_role_required("student", "teacher", "admin")
def get_my_submission(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user.is_student() and not _ensure_student_enrolled_for_assignment(user, assignment):
        return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    submission = Submission.query.filter_by(
        assignmentID=assignment_id,
        studentID=user.id,
    ).first()

    if not submission and user.is_student():
        submission = _get_group_submission(user.id, assignment)

    return jsonify({"submission": _attachment_payload(submission) if submission else None}), 200


@bp.route("/<int:assignment_id>/mine", methods=["POST"])
@jwt_role_required("student")
def upload_my_submission(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not _ensure_student_enrolled_for_assignment(user, assignment):
        return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    upload = request.files.get("file")
    if upload is None or not upload.filename:
        return jsonify({"msg": "No file provided"}), 400

    filename = secure_filename(upload.filename)
    if not filename:
        return jsonify({"msg": "Invalid file name"}), 400

    if not _is_allowed_filename(filename):
        return jsonify({"msg": "Unsupported file type"}), 400

    upload.seek(0, os.SEEK_END)
    file_size = upload.tell()
    upload.seek(0)
    if file_size > MAX_FILE_SIZE_BYTES:
        return jsonify({"msg": "File is too large (max 20MB)"}), 400

    assignment_dir = os.path.join(_uploads_root(), f"assignment_{assignment_id}")
    os.makedirs(assignment_dir, exist_ok=True)

    random_suffix = secrets.token_hex(8)
    stored_filename = f"user_{user.id}_{random_suffix}_{filename}"
    stored_path = os.path.join(assignment_dir, stored_filename)
    upload.save(stored_path)

    submission = Submission.query.filter_by(
        assignmentID=assignment_id,
        studentID=user.id,
    ).first()

    if not submission:
        submission = _get_group_submission(user.id, assignment)

    if submission is None:
        submission = Submission(path=stored_path, studentID=user.id, assignmentID=assignment_id)
        db.session.add(submission)
    else:
        _delete_file_if_exists(submission.path)
        submission.path = stored_path
        submission.studentID = user.id

    db.session.commit()
    return jsonify({"msg": "Attachment saved", "submission": _attachment_payload(submission)}), 200


@bp.route("/<int:assignment_id>/mine", methods=["DELETE"])
@jwt_role_required("student")
def delete_my_submission(assignment_id):
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not _ensure_student_enrolled_for_assignment(user, assignment):
        return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    submission = Submission.query.filter_by(
        assignmentID=assignment_id,
        studentID=user.id,
    ).first()

    if not submission:
        submission = _get_group_submission(user.id, assignment)

    if submission is None:
        return jsonify({"msg": "No attachment found"}), 404

    _delete_file_if_exists(submission.path)
    db.session.delete(submission)
    db.session.commit()

    return jsonify({"msg": "Attachment removed"}), 200


@bp.route("/file/<int:submission_id>", methods=["GET"])
@jwt_role_required("student", "teacher", "admin")
def download_submission_file(submission_id):
    submission = Submission.get_by_id(submission_id)
    if not submission or not submission.path:
        return jsonify({"msg": "Attachment not found"}), 404

    assignment = Assignment.get_by_id(submission.assignmentID)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    user = _get_current_user()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if user.is_student():
        if not _ensure_student_enrolled_for_assignment(user, assignment):
            return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403
        if submission.studentID != user.id:
            group_sub = _get_group_submission(user.id, assignment)
            if not group_sub or group_sub.id != submission.id:
                return jsonify({"msg": "Unauthorized"}), 403

    file_path = Path(submission.path)
    if not file_path.exists():
        return jsonify({"msg": "Attachment file is missing"}), 404

    return send_from_directory(file_path.parent, file_path.name, as_attachment=True)