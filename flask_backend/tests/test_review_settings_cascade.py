"""
Tests for cascade delete when disabling review type settings.

When a teacher disables individual_reviews or group_reviews on an assignment,
the corresponding rubric and all reviews of that type should be deleted.

Covers:
  PATCH /assignment/edit_assignment/<id> — cascade behavior when toggling review settings
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    CriteriaDescription,
    Review,
    Rubric,
    User,
    User_Course,
)
from api.models.criterion_model import Criterion
from api.models.db import db as _db


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def teacher(db):
    """Create a teacher user."""
    user = User(
        name="Settings Teacher",
        email="settings_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def students(db):
    """Create two student users."""
    s1 = User(name="Alice", email="settings_alice@test.com", hash_pass=generate_password_hash("pw"), role="student")
    s2 = User(name="Bob", email="settings_bob@test.com", hash_pass=generate_password_hash("pw"), role="student")
    db.session.add_all([s1, s2])
    db.session.commit()
    return s1, s2


@pytest.fixture
def course(db, teacher):
    """Create a course owned by the teacher."""
    c = Course(teacherID=teacher.id, name="Settings Course")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def assignment(db, course):
    """Create an assignment with both review types enabled."""
    a = Assignment(
        courseID=course.id,
        name="Settings HW",
        individual_reviews=True,
        group_reviews=True,
    )
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def individual_rubric_with_reviews(db, assignment, students):
    """Create an individual rubric with criteria and a submitted review."""
    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="individual")
    db.session.add(rubric)
    db.session.flush()

    crit = CriteriaDescription(rubricID=rubric.id, question="Quality", scoreMax=5, hasScore=True)
    db.session.add(crit)
    db.session.flush()

    s1, s2 = students
    review = Review(
        assignmentID=assignment.id,
        reviewerID=s1.id,
        revieweeID=s2.id,
        review_type="individual",
        comments="Good work",
    )
    db.session.add(review)
    db.session.flush()

    db.session.add(Criterion(reviewID=review.id, criterionRowID=crit.id, grade=4))
    db.session.commit()

    return rubric, crit, review


@pytest.fixture
def group_rubric_with_reviews(db, assignment, students):
    """Create a group rubric with criteria and a submitted review."""
    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="group")
    db.session.add(rubric)
    db.session.flush()

    crit = CriteriaDescription(rubricID=rubric.id, question="Teamwork", scoreMax=10, hasScore=True)
    db.session.add(crit)
    db.session.flush()

    s1, _ = students
    review = Review(
        assignmentID=assignment.id,
        reviewerID=s1.id,
        revieweeID=99,  # group ID placeholder
        review_type="group",
        comments="Nice teamwork",
    )
    db.session.add(review)
    db.session.flush()

    db.session.add(Criterion(reviewID=review.id, criterionRowID=crit.id, grade=8))
    db.session.commit()

    return rubric, crit, review


@pytest.fixture
def auth_teacher(test_client, teacher):
    """Log in as teacher — cookie is set on the test client."""
    test_client.post("/auth/login", json={"email": teacher.email, "password": "password123"})
    return test_client


# ============================================================================
# PATCH /assignment/edit_assignment/<id> — DISABLE INDIVIDUAL REVIEWS
# ============================================================================


class TestDisableIndividualReviews:
    """Tests for cascade delete when disabling individual reviews."""

    def test_disabling_individual_reviews_deletes_rubric(
        self, auth_teacher, assignment, individual_rubric_with_reviews
    ):
        """Disabling individual_reviews deletes the individual rubric."""
        rubric, _, _ = individual_rubric_with_reviews
        rubric_id = rubric.id

        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"individual_reviews": False},
        )
        assert resp.status_code == 200

        assert Rubric.get_by_id(rubric_id) is None

    def test_disabling_individual_reviews_deletes_reviews(
        self, auth_teacher, assignment, individual_rubric_with_reviews
    ):
        """Disabling individual_reviews deletes all individual reviews."""
        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"individual_reviews": False},
        )
        assert resp.status_code == 200

        remaining = Review.query.filter_by(
            assignmentID=assignment.id, review_type="individual"
        ).count()
        assert remaining == 0

    def test_disabling_individual_reviews_preserves_group_data(
        self, auth_teacher, assignment, individual_rubric_with_reviews, group_rubric_with_reviews
    ):
        """Disabling individual_reviews does NOT affect group rubric or reviews."""
        group_rubric, _, group_review = group_rubric_with_reviews

        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"individual_reviews": False},
        )
        assert resp.status_code == 200

        assert Rubric.get_by_id(group_rubric.id) is not None
        assert Review.get_by_id(group_review.id) is not None

    def test_disabling_individual_reviews_returns_deleted_counts(
        self, auth_teacher, assignment, individual_rubric_with_reviews
    ):
        """Response includes counts of deleted reviews and rubrics."""
        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"individual_reviews": False},
        )
        assert resp.status_code == 200
        data = resp.json
        assert data.get("individual_reviews_deleted", 0) == 1
        assert data.get("individual_rubric_deleted", False) is True


# ============================================================================
# PATCH /assignment/edit_assignment/<id> — DISABLE GROUP REVIEWS
# ============================================================================


class TestDisableGroupReviews:
    """Tests for cascade delete when disabling group reviews."""

    def test_disabling_group_reviews_deletes_rubric(
        self, auth_teacher, assignment, group_rubric_with_reviews
    ):
        """Disabling group_reviews deletes the group rubric."""
        rubric, _, _ = group_rubric_with_reviews
        rubric_id = rubric.id

        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"group_reviews": False},
        )
        assert resp.status_code == 200

        assert Rubric.get_by_id(rubric_id) is None

    def test_disabling_group_reviews_deletes_reviews(
        self, auth_teacher, assignment, group_rubric_with_reviews
    ):
        """Disabling group_reviews deletes all group reviews."""
        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"group_reviews": False},
        )
        assert resp.status_code == 200

        remaining = Review.query.filter_by(
            assignmentID=assignment.id, review_type="group"
        ).count()
        assert remaining == 0

    def test_disabling_group_reviews_preserves_individual_data(
        self, auth_teacher, assignment, individual_rubric_with_reviews, group_rubric_with_reviews
    ):
        """Disabling group_reviews does NOT affect individual rubric or reviews."""
        ind_rubric, _, ind_review = individual_rubric_with_reviews

        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"group_reviews": False},
        )
        assert resp.status_code == 200

        assert Rubric.get_by_id(ind_rubric.id) is not None
        assert Review.get_by_id(ind_review.id) is not None


# ============================================================================
# EDGE CASES
# ============================================================================


class TestReviewSettingsEdgeCases:
    """Edge cases for review settings cascade."""

    def test_disabling_with_no_rubric_or_reviews(self, auth_teacher, assignment):
        """Disabling a review type with no rubric or reviews succeeds without error."""
        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"individual_reviews": False},
        )
        assert resp.status_code == 200

    def test_enabling_does_not_delete_anything(
        self, auth_teacher, db, assignment, individual_rubric_with_reviews
    ):
        """Re-enabling a review type (true→true) does not delete anything."""
        rubric, _, review = individual_rubric_with_reviews

        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"individual_reviews": True},
        )
        assert resp.status_code == 200

        assert Rubric.get_by_id(rubric.id) is not None
        assert Review.get_by_id(review.id) is not None

    def test_disabling_both_types_at_once(
        self, auth_teacher, assignment, individual_rubric_with_reviews, group_rubric_with_reviews
    ):
        """Disabling both review types in one request deletes both rubrics and all reviews."""
        ind_rubric, _, _ = individual_rubric_with_reviews
        grp_rubric, _, _ = group_rubric_with_reviews

        resp = auth_teacher.patch(
            f"/assignment/edit_assignment/{assignment.id}",
            json={"individual_reviews": False, "group_reviews": False},
        )
        assert resp.status_code == 200

        assert Rubric.get_by_id(ind_rubric.id) is None
        assert Rubric.get_by_id(grp_rubric.id) is None
        assert Review.query.filter_by(assignmentID=assignment.id).count() == 0
