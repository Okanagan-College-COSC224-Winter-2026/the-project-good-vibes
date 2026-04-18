"""Review tracking service — determines which reviewees user has already reviewed."""

from ..models import Assignment, Group_Members, Review
from .group_service import get_user_group_in_course


def get_already_reviewed_reviewees(user, assignment_id, review_type="individual"):
    """Return list of reviewee IDs that the user has already reviewed for this assignment.

    For individual reviews: returns user IDs the current user reviewed.
    For group reviews: returns group IDs that anyone on the user's group reviewed.

    Args:
        user: User object
        assignment_id: int — which assignment
        review_type: str — "individual" or "group"

    Returns:
        list of reviewee IDs (user IDs for individual, group IDs for group)
    """
    assignment = Assignment.get_by_id(assignment_id)
    if not assignment:
        return []

    if review_type == "group":
        user_group = get_user_group_in_course(user.id, assignment.courseID)
        if not user_group:
            return []

        group_member_ids = [
            m.userID for m in Group_Members.query.filter_by(groupID=user_group.id).all()
        ]
        reviews = Review.query.filter(
            Review.assignmentID == assignment_id,
            Review.reviewerID.in_(group_member_ids),
            Review.review_type == "group",
        ).all()
    else:
        reviews = Review.query.filter_by(
            assignmentID=assignment_id,
            reviewerID=user.id,
            review_type="individual",
        ).all()

    reviewee_ids = list({r.revieweeID for r in reviews})
    return reviewee_ids
