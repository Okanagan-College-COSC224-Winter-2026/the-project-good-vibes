"""
Tests for rubric update and cascade-delete of reviews.

When a teacher updates or deletes a rubric, all reviews for that
assignment+review_type must be deleted because the old criterion IDs
are no longer valid.

TDD: These tests are written FIRST before implementation.
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models import User, Course, Assignment, Rubric, CriteriaDescription, Review
from api.models.criterion_model import Criterion
from api.models.db import db as _db


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def teacher(db):
    t = User(
        name="Cascade Teacher",
        email="cascade_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher",
    )
    db.session.add(t)
    db.session.commit()
    return t


@pytest.fixture
def students(db):
    s1 = User(name="Student A", email="stud_a@test.com", hash_pass=generate_password_hash("pw"), role="student")
    s2 = User(name="Student B", email="stud_b@test.com", hash_pass=generate_password_hash("pw"), role="student")
    db.session.add_all([s1, s2])
    db.session.commit()
    return s1, s2


@pytest.fixture
def course(db, teacher):
    c = Course(teacherID=teacher.id, name="Cascade Course")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def assignment(db, course):
    a = Assignment(courseID=course.id, name="Cascade Assignment", rubric_text="placeholder")
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def rubric_with_criteria(db, assignment):
    """Create an individual rubric with two criteria."""
    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="individual")
    db.session.add(rubric)
    db.session.commit()

    c1 = CriteriaDescription(rubricID=rubric.id, question="Quality", scoreMax=5, hasScore=True)
    c2 = CriteriaDescription(rubricID=rubric.id, question="Effort", scoreMax=5, hasScore=True)
    db.session.add_all([c1, c2])
    db.session.commit()
    return rubric, [c1, c2]


@pytest.fixture
def group_rubric_with_criteria(db, assignment):
    """Create a group rubric with one criterion."""
    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="group")
    db.session.add(rubric)
    db.session.commit()

    c1 = CriteriaDescription(rubricID=rubric.id, question="Collaboration", scoreMax=10, hasScore=True)
    db.session.add(c1)
    db.session.commit()
    return rubric, [c1]


@pytest.fixture
def individual_review(db, assignment, students, rubric_with_criteria):
    """Submit an individual review with criterion scores."""
    s1, s2 = students
    rubric, criteria = rubric_with_criteria

    review = Review(assignmentID=assignment.id, reviewerID=s1.id, revieweeID=s2.id, review_type="individual")
    db.session.add(review)
    db.session.commit()

    for crit in criteria:
        cr = Criterion(reviewID=review.id, criterionRowID=crit.id, grade=4, comments="")
        db.session.add(cr)
    db.session.commit()
    return review


@pytest.fixture
def auth_teacher(test_client, teacher):
    test_client.post("/auth/login", json={"email": teacher.email, "password": "password123"})
    return test_client


# ============================================================================
# DELETE RUBRIC CASCADE TESTS
# ============================================================================


class TestDeleteRubricCascadesReviews:
    """Deleting a rubric should also delete all reviews of matching type for that assignment."""

    def test_delete_individual_rubric_deletes_individual_reviews(
        self, auth_teacher, assignment, rubric_with_criteria, individual_review
    ):
        rubric, _ = rubric_with_criteria
        review_id = individual_review.id

        resp = auth_teacher.delete(f"/rubric/{rubric.id}")
        assert resp.status_code == 200

        data = resp.get_json()
        assert data["reviews_deleted"] >= 1

        # Review should no longer exist
        assert Review.get_by_id(review_id) is None

    def test_delete_individual_rubric_does_not_delete_group_reviews(
        self, auth_teacher, db, assignment, students, rubric_with_criteria, group_rubric_with_criteria
    ):
        """Deleting the individual rubric should leave group reviews intact."""
        s1, s2 = students
        rubric, _ = rubric_with_criteria
        group_rubric, group_criteria = group_rubric_with_criteria

        # Create a group review
        group_review = Review(assignmentID=assignment.id, reviewerID=s1.id, revieweeID=99, review_type="group")
        db.session.add(group_review)
        db.session.commit()
        group_review_id = group_review.id

        resp = auth_teacher.delete(f"/rubric/{rubric.id}")
        assert resp.status_code == 200

        # Group review should still exist
        assert Review.get_by_id(group_review_id) is not None

    def test_delete_rubric_returns_review_count(
        self, auth_teacher, db, assignment, students, rubric_with_criteria
    ):
        """Response should include the number of reviews deleted."""
        s1, s2 = students
        rubric, criteria = rubric_with_criteria

        # Create two reviews
        for reviewer, reviewee in [(s1, s2), (s2, s1)]:
            r = Review(assignmentID=assignment.id, reviewerID=reviewer.id, revieweeID=reviewee.id, review_type="individual")
            db.session.add(r)
            db.session.commit()
            for crit in criteria:
                db.session.add(Criterion(reviewID=r.id, criterionRowID=crit.id, grade=3, comments=""))
            db.session.commit()

        resp = auth_teacher.delete(f"/rubric/{rubric.id}")
        assert resp.status_code == 200
        assert resp.get_json()["reviews_deleted"] == 2

    def test_delete_rubric_with_no_reviews(self, auth_teacher, rubric_with_criteria):
        """Deleting a rubric with no reviews should succeed with count 0."""
        rubric, _ = rubric_with_criteria

        resp = auth_teacher.delete(f"/rubric/{rubric.id}")
        assert resp.status_code == 200
        assert resp.get_json()["reviews_deleted"] == 0


# ============================================================================
# UPDATE RUBRIC TESTS
# ============================================================================


class TestUpdateRubric:
    """PUT /rubric/<id> replaces criteria and cascade-deletes reviews."""

    def test_update_rubric_replaces_criteria(self, auth_teacher, rubric_with_criteria):
        """Updating criteria should replace old criteria with new ones."""
        rubric, old_criteria = rubric_with_criteria
        old_ids = [c.id for c in old_criteria]

        resp = auth_teacher.put(f"/rubric/{rubric.id}", json={
            "canComment": False,
            "criteria": [
                {"question": "New Q1", "scoreMax": 10, "hasScore": True},
                {"question": "New Q2", "scoreMax": 8, "hasScore": True},
                {"question": "New Q3", "scoreMax": 0, "hasScore": False},
            ],
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data["rubric"]["canComment"] is False

        # Old criteria should be gone
        for old_id in old_ids:
            assert CriteriaDescription.get_by_id(old_id) is None

        # New criteria should exist
        new_criteria = CriteriaDescription.query.filter_by(rubricID=rubric.id).all()
        assert len(new_criteria) == 3
        assert {c.question for c in new_criteria} == {"New Q1", "New Q2", "New Q3"}

    def test_update_rubric_cascades_reviews(
        self, auth_teacher, assignment, rubric_with_criteria, individual_review
    ):
        """Updating a rubric should delete all reviews of that type."""
        rubric, _ = rubric_with_criteria
        review_id = individual_review.id

        resp = auth_teacher.put(f"/rubric/{rubric.id}", json={
            "criteria": [{"question": "Replaced", "scoreMax": 5, "hasScore": True}],
        })

        assert resp.status_code == 200
        assert resp.get_json()["reviews_deleted"] >= 1
        assert Review.get_by_id(review_id) is None

    def test_update_rubric_does_not_affect_other_type_reviews(
        self, auth_teacher, db, assignment, students, rubric_with_criteria, group_rubric_with_criteria
    ):
        """Updating individual rubric should not touch group reviews."""
        s1, _ = students
        rubric, _ = rubric_with_criteria

        group_review = Review(assignmentID=assignment.id, reviewerID=s1.id, revieweeID=99, review_type="group")
        db.session.add(group_review)
        db.session.commit()
        group_review_id = group_review.id

        auth_teacher.put(f"/rubric/{rubric.id}", json={
            "criteria": [{"question": "Replaced", "scoreMax": 5, "hasScore": True}],
        })

        assert Review.get_by_id(group_review_id) is not None

    def test_update_rubric_requires_criteria(self, auth_teacher, rubric_with_criteria):
        """Update must include at least one criterion."""
        rubric, _ = rubric_with_criteria

        resp = auth_teacher.put(f"/rubric/{rubric.id}", json={"criteria": []})
        assert resp.status_code == 400

    def test_update_rubric_requires_teacher(self, test_client, db, students, rubric_with_criteria):
        """Students cannot update rubrics."""
        rubric, _ = rubric_with_criteria
        s1, _ = students

        test_client.post("/auth/login", json={"email": s1.email, "password": "pw"})
        resp = test_client.put(f"/rubric/{rubric.id}", json={
            "criteria": [{"question": "Nope", "scoreMax": 5, "hasScore": True}],
        })
        assert resp.status_code == 403

    def test_update_nonexistent_rubric(self, auth_teacher):
        resp = auth_teacher.put("/rubric/99999", json={
            "criteria": [{"question": "Q", "scoreMax": 5, "hasScore": True}],
        })
        assert resp.status_code == 404


# ============================================================================
# REVIEW COUNT ON RUBRIC GET
# ============================================================================


class TestRubricReviewCount:
    """GET /rubric/<id> should include the count of associated reviews."""

    def test_rubric_includes_review_count(
        self, auth_teacher, rubric_with_criteria, individual_review
    ):
        rubric, _ = rubric_with_criteria

        resp = auth_teacher.get(f"/rubric/{rubric.id}")
        assert resp.status_code == 200
        assert resp.get_json()["review_count"] >= 1

    def test_rubric_review_count_zero(self, auth_teacher, rubric_with_criteria):
        rubric, _ = rubric_with_criteria

        resp = auth_teacher.get(f"/rubric/{rubric.id}")
        assert resp.status_code == 200
        assert resp.get_json()["review_count"] == 0
