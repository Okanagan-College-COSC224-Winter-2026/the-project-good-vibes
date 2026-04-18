"""
Tests for GET /review/course/<id>/my-progress endpoint.

Returns per-assignment review completion counts for the current student:
  individual_completed / individual_required  (group members minus self)
  group_completed / group_required            (other groups in the course)
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    CourseGroup,
    Group_Members,
    Review,
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
        name="Progress Teacher",
        email="prog_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_a(db):
    user = User(name="Prog Alice", email="prog_alice@test.com", hash_pass=generate_password_hash("password123"), role="student")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_b(db):
    user = User(name="Prog Bob", email="prog_bob@test.com", hash_pass=generate_password_hash("password123"), role="student")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_c(db):
    user = User(name="Prog Carol", email="prog_carol@test.com", hash_pass=generate_password_hash("password123"), role="student")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_d(db):
    user = User(name="Prog Dave", email="prog_dave@test.com", hash_pass=generate_password_hash("password123"), role="student")
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(db, teacher):
    c = Course(teacherID=teacher.id, name="Progress Course")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def enrolled(db, course, student_a, student_b, student_c, student_d):
    for s in [student_a, student_b, student_c, student_d]:
        db.session.add(User_Course(userID=s.id, courseID=course.id))
    db.session.commit()


@pytest.fixture
def group_alpha(db, course, student_a, student_b, enrolled):
    """Group Alpha: Alice + Bob."""
    g = CourseGroup(name="Alpha", courseID=course.id)
    db.session.add(g)
    db.session.flush()
    db.session.add(Group_Members(userID=student_a.id, groupID=g.id))
    db.session.add(Group_Members(userID=student_b.id, groupID=g.id))
    db.session.commit()
    return g


@pytest.fixture
def group_beta(db, course, student_c, student_d, enrolled):
    """Group Beta: Carol + Dave."""
    g = CourseGroup(name="Beta", courseID=course.id)
    db.session.add(g)
    db.session.flush()
    db.session.add(Group_Members(userID=student_c.id, groupID=g.id))
    db.session.add(Group_Members(userID=student_d.id, groupID=g.id))
    db.session.commit()
    return g


@pytest.fixture
def assignment_1(db, course):
    a = Assignment(courseID=course.id, name="Progress HW1")
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def assignment_2(db, course):
    a = Assignment(courseID=course.id, name="Progress HW2")
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def auth_alice(test_client, student_a):
    test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
    return test_client


@pytest.fixture
def auth_bob(test_client, student_b):
    test_client.post("/auth/login", json={"email": student_b.email, "password": "password123"})
    return test_client


# ============================================================================
# BASIC RESPONSE
# ============================================================================


class TestMyProgressBasic:

    def test_returns_all_assignments(self, auth_alice, course, assignment_1, assignment_2, group_alpha, group_beta):
        resp = auth_alice.get(f"/review/course/{course.id}/my-progress")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data["assignments"]) == 2
        ids = {a["assignment_id"] for a in data["assignments"]}
        assert ids == {assignment_1.id, assignment_2.id}

    def test_zero_progress_when_no_reviews(self, auth_alice, course, assignment_1, group_alpha, group_beta):
        resp = auth_alice.get(f"/review/course/{course.id}/my-progress")
        assert resp.status_code == 200
        a = resp.get_json()["assignments"][0]
        assert a["individual_completed"] == 0
        assert a["individual_required"] == 1  # Bob (same group, minus self)
        assert a["group_completed"] == 0
        assert a["group_required"] == 1  # Beta (one other group)

    def test_requires_auth(self, test_client, course):
        resp = test_client.get(f"/review/course/{course.id}/my-progress")
        assert resp.status_code == 401

    def test_404_for_nonexistent_course(self, auth_alice):
        resp = auth_alice.get("/review/course/99999/my-progress")
        assert resp.status_code == 404


# ============================================================================
# INDIVIDUAL PROGRESS
# ============================================================================


class TestMyProgressIndividual:

    def test_counts_individual_reviews(self, auth_alice, db, course, assignment_1, student_a, student_b, group_alpha, group_beta):
        """Alice reviewed Bob → individual_completed should be 1."""
        db.session.add(Review(
            assignmentID=assignment_1.id, reviewerID=student_a.id,
            revieweeID=student_b.id, review_type="individual",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/course/{course.id}/my-progress")
        a = resp.get_json()["assignments"][0]
        assert a["individual_completed"] == 1
        assert a["individual_required"] == 1

    def test_does_not_count_other_users_reviews(self, auth_alice, db, course, assignment_1, student_b, student_c, group_alpha, group_beta):
        """Bob's review of Carol should not count for Alice."""
        db.session.add(Review(
            assignmentID=assignment_1.id, reviewerID=student_b.id,
            revieweeID=student_c.id, review_type="individual",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/course/{course.id}/my-progress")
        a = resp.get_json()["assignments"][0]
        assert a["individual_completed"] == 0


# ============================================================================
# GROUP PROGRESS
# ============================================================================


class TestMyProgressGroup:

    def test_counts_group_reviews(self, auth_alice, db, course, assignment_1, student_a, group_alpha, group_beta):
        """Alice reviewed Group Beta → group_completed should be 1."""
        db.session.add(Review(
            assignmentID=assignment_1.id, reviewerID=student_a.id,
            revieweeID=group_beta.id, review_type="group",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/course/{course.id}/my-progress")
        a = resp.get_json()["assignments"][0]
        assert a["group_completed"] == 1
        assert a["group_required"] == 1

    def test_teammate_review_counts_for_group(self, auth_bob, db, course, assignment_1, student_a, group_alpha, group_beta):
        """Alice (Bob's teammate) reviewed Group Beta → Bob should see group_completed=1."""
        db.session.add(Review(
            assignmentID=assignment_1.id, reviewerID=student_a.id,
            revieweeID=group_beta.id, review_type="group",
        ))
        db.session.commit()

        resp = auth_bob.get(f"/review/course/{course.id}/my-progress")
        a = resp.get_json()["assignments"][0]
        assert a["group_completed"] == 1

    def test_other_group_review_not_counted(self, auth_alice, db, course, assignment_1, student_c, group_alpha, group_beta):
        """Carol (Group Beta) reviewed Group Alpha → should not count for Alice (Group Alpha)."""
        db.session.add(Review(
            assignmentID=assignment_1.id, reviewerID=student_c.id,
            revieweeID=group_alpha.id, review_type="group",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/course/{course.id}/my-progress")
        a = resp.get_json()["assignments"][0]
        assert a["group_completed"] == 0


# ============================================================================
# NO GROUP MEMBERSHIP
# ============================================================================


class TestMyProgressNoGroup:

    def test_student_not_in_group(self, db, test_client, course, assignment_1):
        """Student not in any group gets 0 required for both types."""
        lonely = User(name="Lonely", email="prog_lonely@test.com", hash_pass=generate_password_hash("password123"), role="student")
        db.session.add(lonely)
        db.session.flush()
        db.session.add(User_Course(userID=lonely.id, courseID=course.id))
        db.session.commit()

        test_client.post("/auth/login", json={"email": lonely.email, "password": "password123"})
        resp = test_client.get(f"/review/course/{course.id}/my-progress")
        assert resp.status_code == 200
        a = resp.get_json()["assignments"][0]
        assert a["individual_required"] == 0
        assert a["group_required"] == 0


# ============================================================================
# MULTI-ASSIGNMENT
# ============================================================================


class TestMyProgressMultiAssignment:

    def test_progress_per_assignment(self, auth_alice, db, course, assignment_1, assignment_2, student_a, student_b, group_alpha, group_beta):
        """Different progress per assignment."""
        # Alice reviewed Bob for HW1 only
        db.session.add(Review(
            assignmentID=assignment_1.id, reviewerID=student_a.id,
            revieweeID=student_b.id, review_type="individual",
        ))
        db.session.commit()

        resp = auth_alice.get(f"/review/course/{course.id}/my-progress")
        assignments = {a["assignment_id"]: a for a in resp.get_json()["assignments"]}
        assert assignments[assignment_1.id]["individual_completed"] == 1
        assert assignments[assignment_2.id]["individual_completed"] == 0
