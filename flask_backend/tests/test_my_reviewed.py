"""
Tests for GET /review/assignment/<id>/my-reviewed endpoint.

Returns the list of reviewee IDs the current user (or their group) has
already reviewed for a given assignment.

Individual: IDs the logged-in user personally reviewed.
Group: IDs of groups that anyone on the user's team has reviewed.
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    CourseGroup,
    CriteriaDescription,
    Group_Members,
    Review,
    Rubric,
    User,
    User_Course,
)
from api.models.db import db as _db


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def teacher(db):
    user = User(
        name="MyReviewed Teacher",
        email="myrev_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_a(db):
    """Reviewer student (Group Alpha)."""
    user = User(
        name="MR Alice",
        email="mr_alice@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_b(db):
    """Reviewee student (Group Alpha, same group as Alice)."""
    user = User(
        name="MR Bob",
        email="mr_bob@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_c(db):
    """Student in Group Beta."""
    user = User(
        name="MR Carol",
        email="mr_carol@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_d(db):
    """Another student in Group Beta."""
    user = User(
        name="MR Dave",
        email="mr_dave@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(db, teacher):
    c = Course(teacherID=teacher.id, name="MyReviewed Course")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def enrolled(db, course, student_a, student_b, student_c, student_d):
    for s in [student_a, student_b, student_c, student_d]:
        db.session.add(User_Course(userID=s.id, courseID=course.id))
    db.session.commit()


@pytest.fixture
def assignment(db, course):
    a = Assignment(courseID=course.id, name="MyReviewed HW", is_anonymous=False)
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def group_alpha(db, course, student_a, student_b, enrolled):
    g = CourseGroup(name="Alpha", courseID=course.id)
    db.session.add(g)
    db.session.flush()
    db.session.add(Group_Members(userID=student_a.id, groupID=g.id))
    db.session.add(Group_Members(userID=student_b.id, groupID=g.id))
    db.session.commit()
    return g


@pytest.fixture
def group_beta(db, course, student_c, student_d, enrolled):
    g = CourseGroup(name="Beta", courseID=course.id)
    db.session.add(g)
    db.session.flush()
    db.session.add(Group_Members(userID=student_c.id, groupID=g.id))
    db.session.add(Group_Members(userID=student_d.id, groupID=g.id))
    db.session.commit()
    return g


@pytest.fixture
def auth_alice(test_client, student_a):
    test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
    return test_client


@pytest.fixture
def auth_bob(test_client, student_b):
    test_client.post("/auth/login", json={"email": student_b.email, "password": "password123"})
    return test_client


@pytest.fixture
def auth_carol(test_client, student_c):
    test_client.post("/auth/login", json={"email": student_c.email, "password": "password123"})
    return test_client


# ============================================================================
# INDIVIDUAL REVIEWS
# ============================================================================


class TestMyReviewedIndividual:
    """GET /review/assignment/<id>/my-reviewed?review_type=individual"""

    def test_returns_empty_when_no_reviews(self, auth_alice, assignment):
        resp = auth_alice.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=individual")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == []

    def test_returns_reviewed_user_ids(self, auth_alice, db, assignment, student_a, student_b, student_c, enrolled):
        """Alice has reviewed Bob and Carol individually."""
        for reviewee in [student_b, student_c]:
            db.session.add(Review(
                assignmentID=assignment.id,
                reviewerID=student_a.id,
                revieweeID=reviewee.id,
                review_type="individual",
            ))
        db.session.commit()

        resp = auth_alice.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=individual")
        assert resp.status_code == 200
        ids = resp.get_json()["reviewee_ids"]
        assert set(ids) == {student_b.id, student_c.id}

    def test_does_not_include_other_users_reviews(self, auth_alice, db, assignment, student_a, student_b, student_c, enrolled):
        """Alice should not see Bob's individual reviews."""
        # Bob reviewed Carol
        db.session.add(Review(
            assignmentID=assignment.id,
            reviewerID=student_b.id,
            revieweeID=student_c.id,
            review_type="individual",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=individual")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == []

    def test_does_not_include_group_reviews(self, auth_alice, db, assignment, student_a, group_alpha, group_beta):
        """Individual endpoint should not return group review targets."""
        db.session.add(Review(
            assignmentID=assignment.id,
            reviewerID=student_a.id,
            revieweeID=group_beta.id,
            review_type="group",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=individual")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == []

    def test_defaults_to_individual(self, auth_alice, db, assignment, student_a, student_b, enrolled):
        """When no review_type param, defaults to individual."""
        db.session.add(Review(
            assignmentID=assignment.id,
            reviewerID=student_a.id,
            revieweeID=student_b.id,
            review_type="individual",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/assignment/{assignment.id}/my-reviewed")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == [student_b.id]


# ============================================================================
# GROUP REVIEWS
# ============================================================================


class TestMyReviewedGroup:
    """GET /review/assignment/<id>/my-reviewed?review_type=group"""

    def test_returns_empty_when_no_group_reviews(self, auth_alice, assignment, group_alpha):
        resp = auth_alice.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=group")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == []

    def test_returns_group_ids_reviewed_by_user(self, auth_alice, db, assignment, student_a, group_alpha, group_beta):
        """Alice (Group Alpha) reviewed Group Beta."""
        db.session.add(Review(
            assignmentID=assignment.id,
            reviewerID=student_a.id,
            revieweeID=group_beta.id,
            review_type="group",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=group")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == [group_beta.id]

    def test_teammate_sees_reviews_submitted_by_groupmate(self, auth_bob, db, assignment, student_a, group_alpha, group_beta):
        """Bob should see Group Beta as reviewed even though Alice submitted it."""
        db.session.add(Review(
            assignmentID=assignment.id,
            reviewerID=student_a.id,  # Alice submitted
            revieweeID=group_beta.id,
            review_type="group",
        ))
        db.session.commit()

        resp = auth_bob.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=group")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == [group_beta.id]

    def test_other_group_does_not_see_review(self, auth_carol, db, assignment, student_a, group_alpha, group_beta):
        """Carol (Group Beta) should NOT see Group Beta in her reviewed list."""
        db.session.add(Review(
            assignmentID=assignment.id,
            reviewerID=student_a.id,  # Alice (Group Alpha) reviewed Group Beta
            revieweeID=group_beta.id,
            review_type="group",
        ))
        db.session.commit()

        resp = auth_carol.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=group")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == []

    def test_user_not_in_group_gets_empty(self, db, test_client, assignment, student_a, enrolled):
        """Student not in any group gets empty list for group reviews."""
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        resp = test_client.get(f"/review/assignment/{assignment.id}/my-reviewed?review_type=group")
        assert resp.status_code == 200
        assert resp.get_json()["reviewee_ids"] == []


# ============================================================================
# AUTH / EDGE CASES
# ============================================================================


class TestMyReviewedAuth:
    def test_requires_authentication(self, test_client, assignment):
        resp = test_client.get(f"/review/assignment/{assignment.id}/my-reviewed")
        assert resp.status_code == 401

    def test_404_for_nonexistent_assignment(self, auth_alice, assignment):
        resp = auth_alice.get("/review/assignment/99999/my-reviewed")
        assert resp.status_code == 404
