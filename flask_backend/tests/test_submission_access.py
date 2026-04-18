"""
Tests for cross-user submission access.

Covers:
  GET /submission/<assignment_id>/student/<student_id> — view another user's submission

Access rules:
  - Teacher/admin: always allowed (must own the course)
  - Student: must be enrolled in the course
  - Returns submission metadata + download URL, or null if no submission exists
"""

import io

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    CourseGroup,
    Group_Members,
    Submission,
    User,
    User_Course,
)
from api.models.db import db as _db


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def teacher(db):
    """Create a teacher user."""
    user = User(
        name="Access Teacher",
        email="access_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_a(db):
    """Create student Alice."""
    user = User(
        name="Alice",
        email="access_alice@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_b(db):
    """Create student Bob."""
    user = User(
        name="Bob",
        email="access_bob@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_c(db):
    """Create student Carol (not enrolled)."""
    user = User(
        name="Carol",
        email="access_carol@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(db, teacher):
    """Create a course owned by the teacher."""
    c = Course(teacherID=teacher.id, name="Access Test Course")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def enrolled(db, course, student_a, student_b):
    """Enroll students A and B in the course."""
    for s in [student_a, student_b]:
        db.session.add(User_Course(userID=s.id, courseID=course.id))
    db.session.commit()


@pytest.fixture
def assignment(db, course):
    """Create an assignment in the course."""
    a = Assignment(courseID=course.id, name="Submission Access HW", is_anonymous=False)
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def alice_submission(test_client, db, assignment, student_a, teacher, enrolled):
    """Upload a submission as Alice and return the submission record."""
    # Login as Alice and upload via API so the file is actually written
    test_client.post(
        "/auth/login", json={"email": student_a.email, "password": "password123"}
    )
    resp = test_client.post(
        f"/submission/{assignment.id}/mine",
        data={"file": (io.BytesIO(b"alice submission content"), "alice_work.txt")},
        content_type="multipart/form-data",
    )
    assert resp.status_code == 200
    return resp.json["submission"]


@pytest.fixture
def auth_teacher(test_client, teacher):
    """Log in as teacher — cookie is set on the test client."""
    test_client.post(
        "/auth/login", json={"email": teacher.email, "password": "password123"}
    )
    return test_client


@pytest.fixture
def auth_student_a(test_client, student_a):
    """Log in as student Alice — cookie is set on the test client."""
    test_client.post(
        "/auth/login", json={"email": student_a.email, "password": "password123"}
    )
    return test_client


@pytest.fixture
def auth_student_b(test_client, student_b):
    """Log in as student Bob — cookie is set on the test client."""
    test_client.post(
        "/auth/login", json={"email": student_b.email, "password": "password123"}
    )
    return test_client


@pytest.fixture
def auth_student_c(test_client, student_c):
    """Log in as student Carol (not enrolled) — cookie is set on the test client."""
    test_client.post(
        "/auth/login", json={"email": student_c.email, "password": "password123"}
    )
    return test_client


# ============================================================================
# GET /submission/<assignment_id>/student/<student_id> — TEACHER ACCESS
# ============================================================================


class TestTeacherSubmissionAccess:
    """Tests for teacher viewing a student's submission."""

    def test_teacher_can_view_student_submission(
        self, auth_teacher, alice_submission, assignment, student_a
    ):
        """Teacher can view any enrolled student's submission metadata."""
        # Re-login as teacher since alice_submission logged in as Alice
        auth_teacher.post(
            "/auth/login",
            json={"email": "access_teacher@test.com", "password": "password123"},
        )
        resp = auth_teacher.get(
            f"/submission/{assignment.id}/student/{student_a.id}"
        )
        assert resp.status_code == 200
        assert resp.json["submission"] is not None
        assert resp.json["submission"]["filename"].endswith("alice_work.txt")

    def test_teacher_gets_null_when_no_submission(
        self, auth_teacher, assignment, student_a, enrolled
    ):
        """Teacher gets null submission when student hasn't submitted."""
        resp = auth_teacher.get(
            f"/submission/{assignment.id}/student/{student_a.id}"
        )
        assert resp.status_code == 200
        assert resp.json["submission"] is None

    def test_teacher_404_for_nonexistent_assignment(
        self, auth_teacher, student_a, enrolled
    ):
        """Returns 404 for a nonexistent assignment."""
        resp = auth_teacher.get(f"/submission/9999/student/{student_a.id}")
        assert resp.status_code == 404


# ============================================================================
# GET /submission/<assignment_id>/student/<student_id> — STUDENT ACCESS
# ============================================================================


class TestStudentSubmissionAccess:
    """Tests for students viewing another student's submission."""

    def test_enrolled_student_can_view_peer_submission(
        self, test_client, alice_submission, assignment, student_a, student_b, enrolled
    ):
        """An enrolled student can view a classmate's submission."""
        # Login as Bob
        test_client.post(
            "/auth/login",
            json={"email": student_b.email, "password": "password123"},
        )
        resp = test_client.get(
            f"/submission/{assignment.id}/student/{student_a.id}"
        )
        assert resp.status_code == 200
        assert resp.json["submission"] is not None
        assert resp.json["submission"]["filename"].endswith("alice_work.txt")

    def test_unenrolled_student_cannot_view_submission(
        self, test_client, alice_submission, assignment, student_a, student_c
    ):
        """A student not enrolled in the course cannot view submissions."""
        test_client.post(
            "/auth/login",
            json={"email": student_c.email, "password": "password123"},
        )
        resp = test_client.get(
            f"/submission/{assignment.id}/student/{student_a.id}"
        )
        assert resp.status_code == 403

    def test_student_gets_null_when_no_submission(
        self, auth_student_a, assignment, student_b, enrolled
    ):
        """Student gets null submission when the target hasn't submitted."""
        resp = auth_student_a.get(
            f"/submission/{assignment.id}/student/{student_b.id}"
        )
        assert resp.status_code == 200
        assert resp.json["submission"] is None
