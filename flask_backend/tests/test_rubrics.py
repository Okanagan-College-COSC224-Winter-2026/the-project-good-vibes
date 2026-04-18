"""
Tests for rubric and criteria management functionality.

A Rubric belongs to an Assignment and contains CriteriaDescription rows.
Teachers create rubrics; students see them when performing peer reviews.

TDD: These tests are written FIRST before implementation.
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models import User, Course, Assignment, Rubric, CriteriaDescription
from api.models.db import db as _db


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def teacher(db):
    """Create a teacher user"""
    teacher = User(
        name="Rubric Teacher",
        email="rubric_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher"
    )
    db.session.add(teacher)
    db.session.commit()
    return teacher


@pytest.fixture
def student(db):
    """Create a student user"""
    student = User(
        name="Rubric Student",
        email="rubric_student@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student"
    )
    db.session.add(student)
    db.session.commit()
    return student


@pytest.fixture
def course(db, teacher):
    """Create a course owned by the teacher"""
    course = Course(teacherID=teacher.id, name="Rubric Test Course")
    db.session.add(course)
    db.session.commit()
    return course


@pytest.fixture
def assignment(db, course):
    """Create an assignment in the course"""
    assignment = Assignment(
        courseID=course.id,
        name="Test Assignment",
        rubric_text="placeholder"
    )
    db.session.add(assignment)
    db.session.commit()
    return assignment


@pytest.fixture
def auth_teacher(test_client, teacher):
    """Log in as teacher — cookie is set on the test client"""
    test_client.post("/auth/login", json={
        "email": teacher.email,
        "password": "password123"
    })
    return test_client


@pytest.fixture
def auth_student(test_client, student):
    """Log in as student — cookie is set on the test client"""
    test_client.post("/auth/login", json={
        "email": student.email,
        "password": "password123"
    })
    return test_client


# ============================================================================
# RUBRIC CREATION
# ============================================================================

def test_create_rubric_as_teacher(auth_teacher, assignment):
    """Teacher can create a rubric for an assignment they own"""
    resp = auth_teacher.post("/rubric/create", json={
        "assignmentID": assignment.id,
        "canComment": True
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["rubric"]["assignmentID"] == assignment.id
    assert data["rubric"]["canComment"] is True


def test_create_rubric_unauthorized_student(auth_student, assignment):
    """Students cannot create rubrics"""
    resp = auth_student.post("/rubric/create", json={
        "assignmentID": assignment.id,
        "canComment": True
    })
    assert resp.status_code == 403


def test_create_rubric_missing_assignment_id(auth_teacher):
    """Creating a rubric without assignmentID fails"""
    resp = auth_teacher.post("/rubric/create", json={
        "canComment": True
    })
    assert resp.status_code == 400


def test_create_rubric_nonexistent_assignment(auth_teacher):
    """Creating a rubric for a nonexistent assignment fails"""
    resp = auth_teacher.post("/rubric/create", json={
        "assignmentID": 9999,
        "canComment": True
    })
    assert resp.status_code == 404


def test_create_rubric_not_course_teacher(auth_teacher, db):
    """Teacher cannot create rubric for an assignment in another teacher's course"""
    other_teacher = User(
        name="Other Teacher",
        email="other_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher"
    )
    db.session.add(other_teacher)
    db.session.commit()

    other_course = Course(teacherID=other_teacher.id, name="Other Course")
    db.session.add(other_course)
    db.session.commit()

    other_assignment = Assignment(
        courseID=other_course.id,
        name="Other Assignment",
        rubric_text="other"
    )
    db.session.add(other_assignment)
    db.session.commit()

    resp = auth_teacher.post("/rubric/create", json={
        "assignmentID": other_assignment.id,
        "canComment": True
    })
    assert resp.status_code == 403


# ============================================================================
# RUBRIC RETRIEVAL
# ============================================================================

def test_get_rubric_by_id(auth_teacher, assignment):
    """Get a rubric by its ID"""
    # Create rubric first
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    resp = auth_teacher.get(f"/rubric/{rubric.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["id"] == rubric.id
    assert data["assignmentID"] == assignment.id


def test_get_rubric_not_found(auth_teacher):
    """Getting a nonexistent rubric returns 404"""
    resp = auth_teacher.get("/rubric/9999")
    assert resp.status_code == 404


def test_get_rubric_for_assignment(auth_teacher, assignment):
    """Get the rubric attached to a specific assignment"""
    rubric = Rubric(assignmentID=assignment.id, canComment=False)
    Rubric.create_rubric(rubric)

    resp = auth_teacher.get(f"/rubric/assignment/{assignment.id}")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["assignmentID"] == assignment.id
    assert data["canComment"] is False


def test_get_rubric_for_assignment_none_exists(auth_teacher, assignment):
    """Getting rubric for an assignment with no rubric returns 404"""
    resp = auth_teacher.get(f"/rubric/assignment/{assignment.id}")
    assert resp.status_code == 404


# ============================================================================
# CRITERIA MANAGEMENT
# ============================================================================

def test_add_criterion_to_rubric(auth_teacher, assignment):
    """Teacher can add a criterion (question) to a rubric"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    resp = auth_teacher.post(f"/rubric/{rubric.id}/criteria", json={
        "question": "How well did the student communicate?",
        "scoreMax": 10,
        "hasScore": True
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data["criterion"]["question"] == "How well did the student communicate?"
    assert data["criterion"]["scoreMax"] == 10
    assert data["criterion"]["hasScore"] is True


def test_add_criterion_missing_question(auth_teacher, assignment):
    """Adding a criterion without a question fails"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    resp = auth_teacher.post(f"/rubric/{rubric.id}/criteria", json={
        "scoreMax": 10,
        "hasScore": True
    })
    assert resp.status_code == 400


def test_add_criterion_nonexistent_rubric(auth_teacher):
    """Adding a criterion to a nonexistent rubric fails"""
    resp = auth_teacher.post("/rubric/9999/criteria", json={
        "question": "Test question",
        "scoreMax": 10,
        "hasScore": True
    })
    assert resp.status_code == 404


def test_add_criterion_unauthorized_student(auth_student, assignment):
    """Students cannot add criteria"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    resp = auth_student.post(f"/rubric/{rubric.id}/criteria", json={
        "question": "Test question",
        "scoreMax": 10,
        "hasScore": True
    })
    assert resp.status_code == 403


def test_get_criteria_for_rubric(auth_teacher, assignment):
    """Get all criteria for a rubric"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    # Add two criteria
    c1 = CriteriaDescription(rubricID=rubric.id, question="Communication", scoreMax=10, hasScore=True)
    c2 = CriteriaDescription(rubricID=rubric.id, question="Teamwork", scoreMax=5, hasScore=True)
    CriteriaDescription.create_criteria_description(c1)
    CriteriaDescription.create_criteria_description(c2)

    resp = auth_teacher.get(f"/rubric/{rubric.id}/criteria")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data) == 2
    questions = [c["question"] for c in data]
    assert "Communication" in questions
    assert "Teamwork" in questions


def test_get_criteria_empty_rubric(auth_teacher, assignment):
    """Getting criteria for a rubric with none returns empty list"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    resp = auth_teacher.get(f"/rubric/{rubric.id}/criteria")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data == []


def test_get_criteria_nonexistent_rubric(auth_teacher):
    """Getting criteria for a nonexistent rubric returns 404"""
    resp = auth_teacher.get("/rubric/9999/criteria")
    assert resp.status_code == 404


# ============================================================================
# RUBRIC DELETION
# ============================================================================

def test_delete_rubric(auth_teacher, assignment):
    """Teacher can delete a rubric"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    resp = auth_teacher.delete(f"/rubric/{rubric.id}")
    assert resp.status_code == 200

    # Verify it's gone
    assert Rubric.get_by_id(rubric.id) is None


def test_delete_rubric_cascades_criteria(auth_teacher, assignment):
    """Deleting a rubric also deletes its criteria"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    c1 = CriteriaDescription(rubricID=rubric.id, question="Q1", scoreMax=10)
    c2 = CriteriaDescription(rubricID=rubric.id, question="Q2", scoreMax=5)
    CriteriaDescription.create_criteria_description(c1)
    CriteriaDescription.create_criteria_description(c2)
    c1_id, c2_id = c1.id, c2.id

    resp = auth_teacher.delete(f"/rubric/{rubric.id}")
    assert resp.status_code == 200

    # Criteria should be gone too
    assert CriteriaDescription.get_by_id(c1_id) is None
    assert CriteriaDescription.get_by_id(c2_id) is None


def test_delete_rubric_not_found(auth_teacher):
    """Deleting a nonexistent rubric returns 404"""
    resp = auth_teacher.delete("/rubric/9999")
    assert resp.status_code == 404


def test_delete_rubric_unauthorized_student(auth_student, assignment):
    """Students cannot delete rubrics"""
    rubric = Rubric(assignmentID=assignment.id, canComment=True)
    Rubric.create_rubric(rubric)

    resp = auth_student.delete(f"/rubric/{rubric.id}")
    assert resp.status_code == 403


# ============================================================================
# FULL WORKFLOW
# ============================================================================

def test_full_rubric_workflow(auth_teacher, assignment):
    """End-to-end: create rubric, add criteria, retrieve everything"""
    # 1. Create rubric
    resp = auth_teacher.post("/rubric/create", json={
        "assignmentID": assignment.id,
        "canComment": True
    })
    assert resp.status_code == 201
    rubric_id = resp.get_json()["rubric"]["id"]

    # 2. Add criteria
    for q, score in [("Communication", 10), ("Teamwork", 10), ("Quality", 5)]:
        resp = auth_teacher.post(f"/rubric/{rubric_id}/criteria", json={
            "question": q,
            "scoreMax": score,
            "hasScore": True
        })
        assert resp.status_code == 201

    # 3. Retrieve criteria
    resp = auth_teacher.get(f"/rubric/{rubric_id}/criteria")
    assert resp.status_code == 200
    criteria = resp.get_json()
    assert len(criteria) == 3

    # 4. Retrieve rubric by assignment
    resp = auth_teacher.get(f"/rubric/assignment/{assignment.id}")
    assert resp.status_code == 200
    assert resp.get_json()["id"] == rubric_id

    # 5. Delete rubric (cleans up criteria too)
    resp = auth_teacher.delete(f"/rubric/{rubric_id}")
    assert resp.status_code == 200

    # 6. Verify everything is gone
    resp = auth_teacher.get(f"/rubric/{rubric_id}")
    assert resp.status_code == 404
    resp = auth_teacher.get(f"/rubric/{rubric_id}/criteria")
    assert resp.status_code == 404
