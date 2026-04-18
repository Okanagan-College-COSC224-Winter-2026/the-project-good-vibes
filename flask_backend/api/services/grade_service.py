"""Grade calculation service — aggregates review scores into grade summaries."""

from ..models import Criterion, CriteriaDescription, Review, Rubric
from .group_service import get_user_group_in_course


def compute_max_score(assignment_id, rubric_type="individual"):
    """Compute the max possible score for an assignment from its rubric criteria.

    Sums scoreMax across all CriteriaDescription rows for the rubric
    of the given type. Returns None if no rubric exists.

    Args:
        assignment_id: int
        rubric_type: str — "individual" or "group"

    Returns:
        int (max score) or None
    """
    rubric = Rubric.query.filter_by(
        assignmentID=assignment_id, rubric_type=rubric_type
    ).first()
    if not rubric:
        return None

    descriptions = CriteriaDescription.query.filter_by(rubricID=rubric.id).all()
    if not descriptions:
        return None

    total = sum(d.scoreMax for d in descriptions if d.scoreMax is not None)
    return total if total > 0 else None


def compute_review_totals(reviews):
    """Extract and sum scored criteria from a list of reviews.

    For each review, sums the grades of all criteria with scores.
    Returns list of totals (one per review).

    Args:
        reviews: list of Review objects

    Returns:
        list of ints (one total per review)
    """
    totals = []
    for review in reviews:
        criteria = Criterion.query.filter_by(reviewID=review.id).all()
        scored = [c for c in criteria if c.grade is not None]
        if scored:
            totals.append(sum(c.grade for c in scored))
    return totals


def compute_course_summary(user, course_id, assignments, target_student_id=None):
    """Compute comprehensive grade summary for a course or specific student.

    Calculates individual and group averages, per-assignment breakdowns,
    and course totals.

    For students (target_student_id == user.id):
    - Individual average: reviews *they received*
    - Group average: reviews *their group received*

    For teachers (target_student_id != user.id or None):
    - Individual average: all individual reviews for the course
    - Group average: all group reviews for the course

    Args:
        user: User object (for group lookup if target_student_id provided)
        course_id: int
        assignments: list of Assignment objects from the course
        target_student_id: int (optional) — if set, scope to that student's grades

    Returns:
        dict with:
        {
            "assignments": [...],
            "individualAverage": float | None,
            "individualMax": float | None,
            "groupAverage": float | None,
            "groupMax": float | None,
            "courseAverage": float | None,
            "courseMax": float | None,
        }
    """
    # Determine target student's group for group review lookups
    target_group = None
    if target_student_id:
        target_group = get_user_group_in_course(target_student_id, course_id)

    assignment_summaries = []

    # Track per-type averages across all assignments
    individual_assignment_avgs = []
    individual_max_values = []
    group_assignment_avgs = []
    group_max_values = []

    for assignment in assignments:
        # --- Individual reviews ---
        if target_student_id:
            ind_reviews = Review.query.filter_by(
                assignmentID=assignment.id,
                revieweeID=target_student_id,
                review_type="individual",
            ).all()
        else:
            ind_reviews = Review.query.filter_by(
                assignmentID=assignment.id, review_type="individual"
            ).all()

        ind_totals = compute_review_totals(ind_reviews)
        ind_avg = sum(ind_totals) / len(ind_totals) if ind_totals else None
        ind_max = compute_max_score(assignment.id, "individual")

        if ind_avg is not None:
            individual_assignment_avgs.append(ind_avg)
            if ind_max is not None:
                individual_max_values.append(ind_max)

        # --- Group reviews ---
        if target_group:
            grp_reviews = Review.query.filter_by(
                assignmentID=assignment.id,
                revieweeID=target_group.id,
                review_type="group",
            ).all()
        elif target_student_id and not target_group:
            grp_reviews = []
        else:
            grp_reviews = Review.query.filter_by(
                assignmentID=assignment.id, review_type="group"
            ).all()

        grp_totals = compute_review_totals(grp_reviews)
        grp_avg = sum(grp_totals) / len(grp_totals) if grp_totals else None
        grp_max = compute_max_score(assignment.id, "group")

        if grp_avg is not None:
            group_assignment_avgs.append(grp_avg)
            if grp_max is not None:
                group_max_values.append(grp_max)

        assignment_summaries.append(
            {
                "id": assignment.id,
                "name": assignment.name,
                "individualReviewCount": len(ind_reviews),
                "individualAverage": round(ind_avg, 2) if ind_avg is not None else None,
                "individualMax": ind_max,
                "groupReviewCount": len(grp_reviews),
                "groupAverage": round(grp_avg, 2) if grp_avg is not None else None,
                "groupMax": grp_max,
            }
        )

    # Compute per-type course totals (sum of scores / sum of maxes)
    ind_course_avg = sum(individual_assignment_avgs) if individual_assignment_avgs else None
    ind_course_max = sum(individual_max_values) if individual_max_values else None
    grp_course_avg = sum(group_assignment_avgs) if group_assignment_avgs else None
    grp_course_max = sum(group_max_values) if group_max_values else None

    # Course total: sum all points earned / sum all points possible
    course_avg_parts = []
    course_max_parts = []
    if ind_course_avg is not None:
        course_avg_parts.append(ind_course_avg)
        if ind_course_max is not None:
            course_max_parts.append(ind_course_max)
    if grp_course_avg is not None:
        course_avg_parts.append(grp_course_avg)
        if grp_course_max is not None:
            course_max_parts.append(grp_course_max)

    course_avg = sum(course_avg_parts) if course_avg_parts else None
    course_max = sum(course_max_parts) if course_max_parts else None

    return {
        "assignments": assignment_summaries,
        "individualAverage": round(ind_course_avg, 2) if ind_course_avg is not None else None,
        "individualMax": round(ind_course_max, 2) if ind_course_max is not None else None,
        "groupAverage": round(grp_course_avg, 2) if grp_course_avg is not None else None,
        "groupMax": round(grp_course_max, 2) if grp_course_max is not None else None,
        "courseAverage": round(course_avg, 2) if course_avg is not None else None,
        "courseMax": round(course_max, 2) if course_max is not None else None,
    }
