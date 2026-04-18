"""Review masking service — handles anonymity and reviewer identity transformation."""

from ..models import Assignment, User
from .group_service import get_user_group_in_course


def mask_reviewer(review, assignment, is_teacher, course_id, viewing_user_id=None):
    """Mask or transform reviewer identity based on assignment anonymity and review type.

    For students viewing reviews:
    - If viewing their own review: always show real reviewer identity
    - If reviewing anonymously: show {"id": None, "name": "Anonymous", "email": None}
    - Individual non-anonymous: show real reviewer
    - Group anonymous: show {"id": None, "name": "Anonymous", "email": None}
    - Group non-anonymous: show {"id": None, "name": "<GroupName>", "email": None}

    For teachers: always show real reviewer.

    Args:
        review: Review object with reviewerID, review_type
        assignment: Assignment object with is_anonymous flag
        is_teacher: bool — True if current user is teacher/admin
        course_id: int — course ID for group lookup
        viewing_user_id: int (optional) — ID of user viewing the review

    Returns:
        dict with {"id", "name", "email"} or None if no transformation needed
    """
    if is_teacher:
        return None  # Teachers always see real reviewer, no masking

    # If viewing own review, always show real identity
    if viewing_user_id and viewing_user_id == review.reviewerID:
        return None

    # Individual review anonymity
    if review.review_type == "individual":
        if assignment.is_anonymous:
            return {"id": None, "name": "Anonymous", "email": None}
        return None  # Show real reviewer

    # Group review anonymity
    if review.review_type == "group":
        if assignment.is_anonymous:
            return {"id": None, "name": "Anonymous", "email": None}
        else:
            # Show group name instead of individual
            reviewer_group = get_user_group_in_course(review.reviewerID, course_id)
            return {
                "id": None,
                "name": reviewer_group.name if reviewer_group else "Unknown Group",
                "email": None,
            }

    return None

