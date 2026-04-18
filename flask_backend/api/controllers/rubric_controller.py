"""
Rubric and Criteria controller for the peer evaluation app.

Endpoints:
  POST   /rubric/create                  — Create a rubric for an assignment
  GET    /rubric/<id>                    — Get a rubric by ID (includes review_count)
  GET    /rubric/assignment/<id>         — Get the rubric for an assignment
  PUT    /rubric/<id>                    — Update rubric (replace criteria, cascade-delete reviews)
  DELETE /rubric/<id>                    — Delete a rubric (cascade criteria + reviews)
  POST   /rubric/<id>/criteria           — Add a criterion to a rubric
  GET    /rubric/<id>/criteria           — List criteria for a rubric
"""

from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from ..models import (
    Assignment,
    Course,
    CriteriaDescription,
    CriteriaDescriptionSchema,
    Rubric,
    RubricSchema,
    User,
)
from ..models.review_model import Review
from ..models.db import db
from .auth_controller import jwt_teacher_required

bp = Blueprint("rubric", __name__, url_prefix="/rubric")


def _delete_reviews_for_rubric(rubric):
    """Delete all reviews matching the rubric's assignment and type.

    Returns the number of reviews deleted.
    """
    review_type = rubric.rubric_type
    reviews = Review.query.filter_by(
        assignmentID=rubric.assignmentID, review_type=review_type
    ).all()
    count = len(reviews)
    for r in reviews:
        db.session.delete(r)
    return count


# ============================================================================
# RUBRIC CRUD
# ============================================================================


@bp.route("/create", methods=["POST"])
@jwt_teacher_required
def create_rubric():
    """Create a rubric for an assignment the teacher owns."""
    data = request.get_json()
    assignment_id = data.get("assignmentID")

    if not assignment_id:
        return jsonify({"msg": "assignmentID is required"}), 400

    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    # Verify the logged-in teacher owns the course
    email = get_jwt_identity()
    user = User.get_by_email(email)
    course = Course.get_by_id(assignment.courseID)
    if course.teacherID != user.id:
        return jsonify({"msg": "Unauthorized: you are not the teacher of this course"}), 403

    can_comment = data.get("canComment", True)
    rubric_type = data.get("rubric_type", "individual")

    if rubric_type not in ("individual", "group"):
        return jsonify({"msg": "rubric_type must be 'individual' or 'group'"}), 400

    rubric = Rubric(assignmentID=assignment_id, canComment=can_comment, rubric_type=rubric_type)
    Rubric.create_rubric(rubric)

    return jsonify({
        "msg": "Rubric created",
        "rubric": RubricSchema().dump(rubric),
    }), 201


@bp.route("/<int:rubric_id>", methods=["GET"])
@jwt_required()
def get_rubric(rubric_id):
    """Get a rubric by its ID, including the count of associated reviews."""
    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    review_count = Review.query.filter_by(
        assignmentID=rubric.assignmentID, review_type=rubric.rubric_type
    ).count()

    result = RubricSchema().dump(rubric)
    result["review_count"] = review_count
    return jsonify(result), 200


@bp.route("/assignment/<int:assignment_id>", methods=["GET"])
@jwt_required()
def get_rubric_for_assignment(assignment_id):
    """Get the rubric attached to an assignment.

    Optional query param ``rubric_type`` filters by type (default: "individual").
    """
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return jsonify({"msg": "Assignment not found"}), 404

    rubric_type = request.args.get("rubric_type", "individual")
    rubric = Rubric.query.filter_by(
        assignmentID=assignment_id, rubric_type=rubric_type
    ).first()
    if not rubric:
        return jsonify({"msg": "No rubric found for this assignment"}), 404

    return jsonify(RubricSchema().dump(rubric)), 200


@bp.route("/<int:rubric_id>", methods=["PUT"])
@jwt_teacher_required
def update_rubric(rubric_id):
    """Update a rubric: replace criteria atomically, cascade-delete reviews.

    All reviews of the matching type for this assignment are deleted because
    the old criterion IDs become invalid.
    """
    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    data = request.get_json()
    criteria_data = data.get("criteria", [])
    if not criteria_data:
        return jsonify({"msg": "At least one criterion is required"}), 400

    # Cascade-delete reviews that reference this rubric's criteria
    reviews_deleted = _delete_reviews_for_rubric(rubric)

    # Delete old criteria one by one so ORM cascades delete Criterion responses
    for old_crit in CriteriaDescription.query.filter_by(rubricID=rubric.id).all():
        db.session.delete(old_crit)

    # Update rubric fields
    if "canComment" in data:
        rubric.canComment = data["canComment"]

    # Create new criteria
    for item in criteria_data:
        has_score = item.get("hasScore", True)
        score_max = item.get("scoreMax", 0)

        if has_score:
            if not isinstance(score_max, int) or score_max < 1 or score_max > 100:
                db.session.rollback()
                return jsonify({"msg": "scoreMax must be an integer between 1 and 100"}), 400
        else:
            score_max = 1

        crit = CriteriaDescription(
            rubricID=rubric.id,
            question=item.get("question", ""),
            scoreMax=score_max,
            hasScore=has_score,
        )
        db.session.add(crit)

    db.session.commit()

    return jsonify({
        "msg": "Rubric updated",
        "rubric": RubricSchema().dump(rubric),
        "reviews_deleted": reviews_deleted,
    }), 200


@bp.route("/<int:rubric_id>", methods=["DELETE"])
@jwt_teacher_required
def delete_rubric(rubric_id):
    """Delete a rubric, cascade-delete its criteria and associated reviews."""
    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    reviews_deleted = _delete_reviews_for_rubric(rubric)
    rubric.delete()

    return jsonify({"msg": "Rubric deleted", "reviews_deleted": reviews_deleted}), 200


# ============================================================================
# CRITERIA CRUD
# ============================================================================


@bp.route("/<int:rubric_id>/criteria", methods=["POST"])
@jwt_teacher_required
def add_criterion(rubric_id):
    """Add a criterion (question row) to a rubric."""
    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    data = request.get_json()
    question = data.get("question")
    if not question:
        return jsonify({"msg": "question is required"}), 400

    score_max = data.get("scoreMax", 0)
    has_score = data.get("hasScore", True)

    if has_score:
        if not isinstance(score_max, int) or score_max < 1 or score_max > 100:
            return jsonify({"msg": "scoreMax must be an integer between 1 and 100"}), 400
    else:
        score_max = 1

    criterion = CriteriaDescription(
        rubricID=rubric_id,
        question=question,
        scoreMax=score_max,
        hasScore=has_score,
    )
    CriteriaDescription.create_criteria_description(criterion)

    return jsonify({
        "msg": "Criterion added",
        "criterion": CriteriaDescriptionSchema().dump(criterion),
    }), 201


@bp.route("/<int:rubric_id>/criteria", methods=["GET"])
@jwt_required()
def get_criteria(rubric_id):
    """List all criteria for a rubric."""
    rubric = Rubric.get_by_id(rubric_id)
    if not rubric:
        return jsonify({"msg": "Rubric not found"}), 404

    criteria = CriteriaDescription.query.filter_by(rubricID=rubric_id).all()
    return jsonify(CriteriaDescriptionSchema(many=True).dump(criteria)), 200
