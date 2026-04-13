"""Progress tracking service — calculates review completion progress per assignment."""

from sqlalchemy import func

from ..models import CourseGroup, Group_Members, Review
from .group_service import get_user_group_in_course


def get_review_progress(user, course_id, assignments):
    """Calculate per-assignment review completion progress for a student.

    For each assignment, returns individual and group review counts
    (completed vs required), only counting enabled review types.

    Args:
        user: User object
        course_id: int
        assignments: list of Assignment objects from the course

    Returns:
        list of dicts: [
            {
                "assignment_id": int,
                "individual_completed": int,
                "individual_required": int,
                "group_completed": int,
                "group_required": int,
            },
            ...
        ]
    """
    # Determine user's group and potential reviewees
    user_group = get_user_group_in_course(user.id, course_id)

    if user_group:
        group_member_ids = [
            m.userID for m in Group_Members.query.filter_by(groupID=user_group.id).all()
        ]
        other_member_ids = [mid for mid in group_member_ids if mid != user.id]
        individual_required = len(other_member_ids)

        all_groups = CourseGroup.query.filter_by(courseID=course_id).all()
        group_required = len([g for g in all_groups if g.id != user_group.id])
    else:
        group_member_ids = []
        individual_required = 0
        group_required = 0

    result = []

    for assignment in assignments:
        # Individual reviews (only if enabled for this assignment)
        if assignment.individual_reviews:
            ind_completed_raw = (
                Review.query.with_entities(func.count(func.distinct(Review.revieweeID)))
                .filter_by(
                    assignmentID=assignment.id,
                    reviewerID=user.id,
                    review_type="individual",
                )
                .scalar()
                or 0
            )
            ind_required = individual_required
            ind_completed = min(int(ind_completed_raw), int(ind_required))
        else:
            ind_completed = 0
            ind_required = 0

        # Group reviews (only if enabled for this assignment)
        if assignment.group_reviews and user_group and group_member_ids:
            grp_completed_raw = (
                Review.query.with_entities(func.count(func.distinct(Review.revieweeID)))
                .filter(
                    Review.assignmentID == assignment.id,
                    Review.reviewerID.in_(group_member_ids),
                    Review.review_type == "group",
                )
                .scalar()
                or 0
            )
            grp_required = group_required
            grp_completed = min(int(grp_completed_raw), int(grp_required))
        else:
            grp_completed = 0
            grp_required = 0

        result.append(
            {
                "assignment_id": assignment.id,
                "individual_completed": ind_completed,
                "individual_required": ind_required,
                "group_completed": grp_completed,
                "group_required": grp_required,
            }
        )

    return result
