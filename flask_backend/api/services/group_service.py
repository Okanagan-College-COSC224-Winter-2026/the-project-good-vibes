"""Group-related utility functions."""

from ..models import CourseGroup, Group_Members


def get_user_group_in_course(user_id, course_id):
    """Return the CourseGroup the user belongs to in this course, or None."""
    membership = (
        Group_Members.query
        .join(CourseGroup, CourseGroup.id == Group_Members.groupID)
        .filter(Group_Members.userID == user_id, CourseGroup.courseID == course_id)
        .first()
    )
    if membership:
        return CourseGroup.get_by_id(membership.groupID)
    return None
