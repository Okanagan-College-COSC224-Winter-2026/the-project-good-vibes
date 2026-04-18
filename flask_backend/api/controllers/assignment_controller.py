from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required
from datetime import datetime, timezone

from ..models import Course, Assignment, User, AssignmentSchema, User_Course, Submission, CourseGroup, Group_Members
from ..models.db import db
from ..models.criterion_model import Criterion
from ..models.review_model import Review
from ..models.rubric_model import Rubric
from ..models.criteria_description_model import CriteriaDescription
from .auth_controller import jwt_teacher_required

bp = Blueprint("assignment", __name__, url_prefix="/assignment")


def _cascade_delete_review_type(assignment, review_type):
    """Delete the rubric and all reviews of the given type for an assignment.

    Called when a teacher disables individual_reviews or group_reviews.
    Returns a dict with counts of deleted items.
    """
    result = {f"{review_type}_rubric_deleted": False, f"{review_type}_reviews_deleted": 0}

    # Delete reviews of this type
    reviews = Review.query.filter_by(
        assignmentID=assignment.id, review_type=review_type
    ).all()
    result[f"{review_type}_reviews_deleted"] = len(reviews)
    for r in reviews:
        db.session.delete(r)

    # Delete the rubric of this type (cascade deletes criteria descriptions)
    rubric = Rubric.query.filter_by(
        assignmentID=assignment.id, rubric_type=review_type
    ).first()
    if rubric:
        # Delete criteria descriptions (which cascade-delete criterion responses)
        for crit in CriteriaDescription.query.filter_by(rubricID=rubric.id).all():
            db.session.delete(crit)
        db.session.delete(rubric)
        result[f"{review_type}_rubric_deleted"] = True

    return result


def _coerce_optional_bool(value, field_name):
    if value is None:
        return None
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    if isinstance(value, int) and value in {0, 1}:
        return bool(value)
    raise ValueError(f"Invalid boolean format for {field_name}.")


def _can_access_course_assignments(user, course):
    if user.is_admin():
        return True
    if course.teacherID == user.id:
        return True
    if user.is_student() and User_Course.get(user.id, course.id):
        return True
    return False

def _normalize_datetime(dt):
    if dt is None:
        return None
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt

@bp.route("/create_assignment", methods=["POST"])
@jwt_teacher_required
def create_assignment():
    """Create a new assignment for a class where the authenticated user is the teacher"""
    data = request.get_json()
    course_id = data.get("courseID")
    assignment_name = data.get("name")
    description = data.get("description")
    start_date = data.get("start_date")
    rubric_text = data.get("rubric")
    due_date = data.get("due_date")
    is_anonymous = data.get("is_anonymous", True)
    individual_reviews = data.get("individual_reviews", True)
    group_reviews = data.get("group_reviews", True)
    

    try:
        if start_date:
            start_date = _normalize_datetime(datetime.fromisoformat(start_date))
        else:
            start_date = None

        if due_date:
            due_date = _normalize_datetime(datetime.fromisoformat(due_date))
        else:
            due_date = None

        if start_date and due_date and start_date > due_date:
            return jsonify({"msg": "Due date cannot be before start date"}), 400

        is_anonymous = _coerce_optional_bool(is_anonymous, "is_anonymous")
        if is_anonymous is None:
            is_anonymous = True

        individual_reviews = _coerce_optional_bool(individual_reviews, "individual_reviews")
        if individual_reviews is None:
            individual_reviews = True

        group_reviews = _coerce_optional_bool(group_reviews, "group_reviews")
        if group_reviews is None:
            group_reviews = True
    except ValueError:
        return jsonify({"msg": "Invalid format. Use ISO format for start_date/due_date and boolean for is_anonymous."}), 400

    if not course_id:
        return jsonify({"msg": "Course ID is required"}), 400
    if not assignment_name:
        return jsonify({"msg": "Assignment name is required"}), 400

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(course_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404
    if course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    new_assignment = Assignment(
        courseID=course_id,
        name=assignment_name,
        description=description,
        start_date=start_date,
        rubric_text=rubric_text,
        due_date=due_date,
        is_anonymous=is_anonymous,
        individual_reviews=individual_reviews,
        group_reviews=group_reviews,
    )
    Assignment.create(new_assignment)
    return (
        jsonify(
            {
                "msg": "Assignment created",
                "assignment": AssignmentSchema().dump(new_assignment),
            }
        ),
        201,
    )

@bp.route("/edit_assignment/<int:assignment_id>", methods=["PATCH"])
@jwt_teacher_required
def edit_assignment(assignment_id):
    """Edit an existing assignment if the authenticated user is the teacher of the class"""
    data = request.get_json()
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if course is None:
        return jsonify({"msg": "Course not found"}), 404
    
    if course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    assignment.name = data.get("name", assignment.name)
    assignment.description = data.get("description", assignment.description)
    assignment.rubric_text = data.get("rubric", assignment.rubric_text)

    try:
        new_start_date = _normalize_datetime(assignment.start_date)
        new_due_date = _normalize_datetime(assignment.due_date)

        start_date = data.get("start_date")
        if start_date:
            new_start_date = _normalize_datetime(datetime.fromisoformat(start_date))

        due_date = data.get("due_date")
        if due_date:
            new_due_date = _normalize_datetime(datetime.fromisoformat(due_date))

        if new_start_date and new_due_date and new_start_date > new_due_date:
            return jsonify({"msg": "Due date cannot be before start date"}), 400

        assignment.start_date = new_start_date
        assignment.due_date = new_due_date

        if "is_anonymous" in data:
            assignment.is_anonymous = _coerce_optional_bool(data.get("is_anonymous"), "is_anonymous")
        if "individual_reviews" in data:
            assignment.individual_reviews = _coerce_optional_bool(data.get("individual_reviews"), "individual_reviews")
        if "group_reviews" in data:
            assignment.group_reviews = _coerce_optional_bool(data.get("group_reviews"), "group_reviews")
    except ValueError:
        return jsonify({"msg": "Invalid format. Use ISO format for start_date/due_date and boolean for is_anonymous."}), 400

    # Cascade delete rubric + reviews when a review type is disabled
    cascade_info = {}
    if "individual_reviews" in data and assignment.individual_reviews is False:
        cascade_info.update(_cascade_delete_review_type(assignment, "individual"))
    if "group_reviews" in data and assignment.group_reviews is False:
        cascade_info.update(_cascade_delete_review_type(assignment, "group"))

    assignment.update()
    return (
        jsonify(
            {
                "msg": "Assignment updated",
                "assignment": AssignmentSchema().dump(assignment),
                **cascade_info,
            }
        ),
        200,
    )
@bp.route("/delete_assignment/<int:assignment_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_assignment(assignment_id):
    """Delete an existing assignment if the authenticated user is the teacher of the class"""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Course not found"}), 404

    if course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: You are not the teacher of this class"}), 403

    try:
        # Criterion has FKs to both Review and CriteriaDescription.
        # Delete all Criterion rows for this assignment first to avoid
        # FK constraint conflicts during cascade.
        review_ids = [r.id for r in assignment.reviews.all()]
        if review_ids:
            Criterion.query.filter(Criterion.reviewID.in_(review_ids)).delete(
                synchronize_session="fetch"
            )

        db.session.delete(assignment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"msg": f"Failed to delete assignment: {str(e)}"}), 500

    return jsonify({"msg": "Assignment deleted"}), 200


@bp.route("/detail/<int:assignment_id>", methods=["GET"])
@jwt_required()
def get_assignment(assignment_id):
    """Get a single assignment by ID"""
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    course = Course.get_by_id(assignment.courseID)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    if not _can_access_course_assignments(user, course):
        return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    return jsonify(AssignmentSchema().dump(assignment)), 200
    

# the following routes are for getting the assignments for a given course
@bp.route("/<int:class_id>", methods=["GET"])
@jwt_required()
def get_assignments(class_id):
    """Get all assignments for a given class"""
    course = Course.get_by_id(class_id)
    if not course:
        return jsonify({"msg": "Class not found"}), 404

    email = get_jwt_identity()
    user = User.get_by_email(email)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not _can_access_course_assignments(user, course):
        return jsonify({"msg": "Unauthorized: You do not have access to this class"}), 403

    assignments = Assignment.get_by_class_id(class_id)
    assignments_data = AssignmentSchema(many=True).dump(assignments)

    # For students, attach has_submitted flag per assignment
    if user.is_student():
        assignment_ids = [a.id for a in assignments]
        # Individual submissions
        submitted_ids = set(
            row.assignmentID for row in
            Submission.query.filter(
                Submission.assignmentID.in_(assignment_ids),
                Submission.studentID == user.id,
            ).with_entities(Submission.assignmentID).all()
        )
        # Group submissions for remaining assignments
        membership = (
            Group_Members.query
            .join(CourseGroup, CourseGroup.id == Group_Members.groupID)
            .filter(Group_Members.userID == user.id, CourseGroup.courseID == class_id)
            .first()
        )
        if membership:
            group_member_ids = [
                m.userID for m in Group_Members.query.filter_by(groupID=membership.groupID).all()
            ]
            remaining = [aid for aid in assignment_ids if aid not in submitted_ids]
            if remaining:
                group_submitted = set(
                    row.assignmentID for row in
                    Submission.query.filter(
                        Submission.assignmentID.in_(remaining),
                        Submission.studentID.in_(group_member_ids),
                    ).with_entities(Submission.assignmentID).all()
                )
                submitted_ids |= group_submitted

        for a_data in assignments_data:
            a_data["has_submitted"] = a_data["id"] in submitted_ids

    return jsonify(assignments_data), 200