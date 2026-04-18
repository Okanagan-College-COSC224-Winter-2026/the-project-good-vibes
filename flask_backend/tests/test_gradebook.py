"""
Tests for the teacher gradebook feature.

Covers:
  - GradeOverride model CRUD
  - GET  /gradebook/course/<id>            — full gradebook data
  - PUT  /gradebook/course/<id>/override   — set/update grade override
  - DELETE /gradebook/course/<id>/override — clear grade override
  - GET  /gradebook/course/<id>/reviews    — reviews for student+assignment
  - Teacher-only access enforcement
"""

import pytest
from werkzeug.security import generate_password_hash

from api.models import (
    Assignment,
    Course,
    CourseGroup,
    CriteriaDescription,
    Criterion,
    Group_Members,
    Review,
    Rubric,
    User,
    User_Course,
)
from api.models.db import db as _db
from api.models.grade_override_model import GradeOverride


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def teacher(db):
    """Create a teacher user."""
    user = User(
        name="Gradebook Teacher",
        email="gb_teacher@test.com",
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
        email="gb_alice@test.com",
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
        email="gb_bob@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(db, teacher):
    """Create a course owned by the teacher."""
    c = Course(teacherID=teacher.id, name="Gradebook Course")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def enrolled(db, course, student_a, student_b):
    """Enroll both students in the course."""
    for s in [student_a, student_b]:
        db.session.add(User_Course(userID=s.id, courseID=course.id))
    db.session.commit()


@pytest.fixture
def assignment(db, course):
    """Create first assignment in the course."""
    a = Assignment(courseID=course.id, name="HW1", is_anonymous=False)
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def assignment2(db, course):
    """Create second assignment in the course."""
    a = Assignment(courseID=course.id, name="HW2", is_anonymous=False)
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def individual_rubric(db, assignment):
    """Create an individual rubric with two criteria (5 pts each, 10 max)."""
    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="individual")
    db.session.add(rubric)
    db.session.flush()
    c1 = CriteriaDescription(rubricID=rubric.id, question="Quality", scoreMax=5, hasScore=True)
    c2 = CriteriaDescription(rubricID=rubric.id, question="Effort", scoreMax=5, hasScore=True)
    db.session.add_all([c1, c2])
    db.session.commit()
    return rubric, [c1, c2]


@pytest.fixture
def group_setup(db, course, student_a, student_b, enrolled, assignment):
    """Create two groups and a group rubric for testing group reviews."""
    group_a = CourseGroup(name="Alpha", courseID=course.id)
    group_b = CourseGroup(name="Beta", courseID=course.id)
    db.session.add_all([group_a, group_b])
    db.session.flush()
    db.session.add(Group_Members(userID=student_a.id, groupID=group_a.id))
    db.session.add(Group_Members(userID=student_b.id, groupID=group_b.id))
    db.session.commit()

    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="group")
    db.session.add(rubric)
    db.session.flush()
    c1 = CriteriaDescription(rubricID=rubric.id, question="Teamwork", scoreMax=10, hasScore=True)
    db.session.add(c1)
    db.session.commit()
    return group_a, group_b, rubric, [c1]


@pytest.fixture
def reviews_for_alice(db, assignment, student_a, student_b, enrolled, individual_rubric):
    """Bob reviews Alice with individual rubric: scores 4 and 3 = 7/10."""
    _, criteria = individual_rubric
    review = Review(
        assignmentID=assignment.id,
        reviewerID=student_b.id,
        revieweeID=student_a.id,
        review_type="individual",
        comments="Good work",
    )
    db.session.add(review)
    db.session.flush()
    db.session.add(Criterion(reviewID=review.id, criterionRowID=criteria[0].id, grade=4))
    db.session.add(Criterion(reviewID=review.id, criterionRowID=criteria[1].id, grade=3))
    db.session.commit()
    return review


@pytest.fixture
def auth_teacher(test_client, teacher):
    """Log in as teacher — cookie is set on the test client."""
    test_client.post("/auth/login", json={"email": teacher.email, "password": "password123"})
    return test_client


@pytest.fixture
def auth_student(test_client, student_a):
    """Log in as student — cookie is set on the test client."""
    test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
    return test_client


# ============================================================================
# GradeOverride MODEL TESTS
# ============================================================================


class TestGradeOverrideModel:
    """CRUD operations and constraints on the GradeOverride model."""

    def test_create_override(self, db, teacher, student_a, course, assignment, enrolled):
        """Teacher can create a grade override for a student."""
        override = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=8.5,
            teacherID=teacher.id,
        )
        db.session.add(override)
        db.session.commit()

        fetched = GradeOverride.query.filter_by(
            studentID=student_a.id, assignmentID=assignment.id
        ).first()
        assert fetched is not None
        assert fetched.override_score == 8.5
        assert fetched.teacherID == teacher.id

    def test_unique_constraint(self, db, teacher, student_a, course, assignment, enrolled):
        """Only one override allowed per student+assignment+course."""
        o1 = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=8.0,
            teacherID=teacher.id,
        )
        db.session.add(o1)
        db.session.commit()

        o2 = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=9.0,
            teacherID=teacher.id,
        )
        db.session.add(o2)
        with pytest.raises(Exception):
            db.session.commit()

    def test_update_override(self, db, teacher, student_a, course, assignment, enrolled):
        """Override score can be updated in place."""
        override = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=7.0,
            teacherID=teacher.id,
        )
        db.session.add(override)
        db.session.commit()

        override.override_score = 9.5
        db.session.commit()

        fetched = GradeOverride.query.get(override.id)
        assert fetched.override_score == 9.5

    def test_delete_override(self, db, teacher, student_a, course, assignment, enrolled):
        """Override can be deleted."""
        override = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=6.0,
            teacherID=teacher.id,
        )
        db.session.add(override)
        db.session.commit()
        oid = override.id

        db.session.delete(override)
        db.session.commit()

        assert GradeOverride.query.get(oid) is None


# ============================================================================
# GET /gradebook/course/<id> — FULL GRADEBOOK
# ============================================================================


class TestGetGradebook:
    """Tests for the full gradebook data endpoint."""

    def test_gradebook_returns_students_and_assignments(
        self, auth_teacher, course, assignment, assignment2, enrolled
    ):
        """Gradebook returns all enrolled students and all assignments."""
        resp = auth_teacher.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 200
        data = resp.json
        assert "assignments" in data
        assert "students" in data
        assert len(data["assignments"]) == 2
        assert len(data["students"]) == 2

    def test_gradebook_shows_peer_review_averages(
        self, auth_teacher, course, assignment, enrolled, reviews_for_alice, student_a
    ):
        """Grades reflect peer review averages when no override is set."""
        resp = auth_teacher.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 200

        alice = next(s for s in resp.json["students"] if s["id"] == student_a.id)
        grade = alice["grades"][str(assignment.id)]
        assert grade["individualAverage"] == 7.0
        assert grade["individualMax"] == 10

    def test_gradebook_shows_override_when_set(
        self, auth_teacher, db, course, assignment, enrolled, reviews_for_alice, student_a, teacher
    ):
        """Override takes precedence as effectiveGrade; peer average is still returned."""
        override = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=9.0,
            teacherID=teacher.id,
        )
        db.session.add(override)
        db.session.commit()

        resp = auth_teacher.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 200

        alice = next(s for s in resp.json["students"] if s["id"] == student_a.id)
        grade = alice["grades"][str(assignment.id)]
        assert grade["overrideScore"] == 9.0
        assert grade["effectiveGrade"] == 9.0
        assert grade["effectiveMax"] == 100.0
        # Peer average should still be present
        assert grade["individualAverage"] == 7.0

    def test_gradebook_max_excludes_types_without_reviews(
        self, auth_teacher, course, assignment, enrolled,
        reviews_for_alice, group_setup, student_a
    ):
        """effectiveMax only counts rubric types where the student has reviews."""
        resp = auth_teacher.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 200

        alice = next(s for s in resp.json["students"] if s["id"] == student_a.id)
        grade = alice["grades"][str(assignment.id)]
        # Alice has individual reviews (7/10) but no group reviews.
        # Equal-weight: only individual counts → 70%
        assert grade["effectiveGrade"] == 70.0
        assert grade["effectiveMax"] == 100.0

    def test_gradebook_includes_course_totals(
        self, auth_teacher, course, assignment, enrolled, reviews_for_alice, student_a
    ):
        """Course totals use equal-weight percentages (out of 100)."""
        resp = auth_teacher.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 200

        alice = next(s for s in resp.json["students"] if s["id"] == student_a.id)
        assert "courseTotal" in alice
        assert alice["courseTotal"]["earned"] == 70.0
        assert alice["courseTotal"]["max"] == 100.0

    def test_gradebook_includes_review_progress(
        self, auth_teacher, db, course, assignment, enrolled,
        student_a, student_b, group_setup, reviews_for_alice
    ):
        """Gradebook response includes reviewProgress and reviewTotal for each student."""
        # student_a and student_b are in separate groups (Alpha, Beta)
        # reviews_for_alice: student_b reviewed student_a (individual)
        # So student_b has completed 1 individual review
        # Each group has 1 member, so individual_required = 0 (no other group members)
        # But there are 2 groups, so group_required = 1 for each student
        resp = auth_teacher.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 200

        for student_row in resp.json["students"]:
            assert "reviewProgress" in student_row, f"Missing reviewProgress for {student_row['name']}"
            assert "reviewTotal" in student_row, f"Missing reviewTotal for {student_row['name']}"
            assert str(assignment.id) in student_row["reviewProgress"]
            progress = student_row["reviewProgress"][str(assignment.id)]
            assert "completed" in progress
            assert "required" in progress

    def test_gradebook_review_progress_counts(
        self, auth_teacher, db, course, assignment, enrolled,
        student_a, student_b
    ):
        """Review progress reflects actual completion vs required counts with multi-member groups."""
        # Create one group with both students so individual_required > 0
        group = CourseGroup(name="Team", courseID=course.id)
        db.session.add(group)
        db.session.flush()
        db.session.add(Group_Members(userID=student_a.id, groupID=group.id))
        db.session.add(Group_Members(userID=student_b.id, groupID=group.id))
        db.session.commit()

        # Create individual rubric
        rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="individual")
        db.session.add(rubric)
        db.session.flush()
        crit = CriteriaDescription(rubricID=rubric.id, question="Q1", scoreMax=5, hasScore=True)
        db.session.add(crit)
        db.session.commit()

        # student_b reviews student_a — so student_b has completed 1/1 individual reviews
        review = Review(
            assignmentID=assignment.id,
            reviewerID=student_b.id,
            revieweeID=student_a.id,
            review_type="individual",
        )
        db.session.add(review)
        db.session.flush()
        db.session.add(Criterion(reviewID=review.id, criterionRowID=crit.id, grade=4))
        db.session.commit()

        resp = auth_teacher.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 200

        bob = next(s for s in resp.json["students"] if s["id"] == student_b.id)
        progress = bob["reviewProgress"][str(assignment.id)]
        assert progress["completed"] == 1
        assert progress["required"] == 1  # 1 other group member
        assert bob["reviewTotal"]["completed"] == 1
        assert bob["reviewTotal"]["required"] == 1

        alice = next(s for s in resp.json["students"] if s["id"] == student_a.id)
        alice_progress = alice["reviewProgress"][str(assignment.id)]
        assert alice_progress["completed"] == 0
        assert alice_progress["required"] == 1  # 1 other group member
        assert alice["reviewTotal"]["completed"] == 0
        assert alice["reviewTotal"]["required"] == 1

    def test_gradebook_teacher_only(self, auth_student, course, enrolled):
        """Students cannot access the gradebook endpoint."""
        resp = auth_student.get(f"/gradebook/course/{course.id}")
        assert resp.status_code == 403

    def test_gradebook_empty_course(self, auth_teacher, db, teacher):
        """Empty course returns empty students and assignments lists."""
        empty_course = Course(teacherID=teacher.id, name="Empty Course")
        db.session.add(empty_course)
        db.session.commit()

        resp = auth_teacher.get(f"/gradebook/course/{empty_course.id}")
        assert resp.status_code == 200
        assert resp.json["students"] == []
        assert resp.json["assignments"] == []


# ============================================================================
# PUT /gradebook/course/<id>/override — SET GRADE OVERRIDE
# ============================================================================


class TestSetOverride:
    """Tests for the set/update grade override endpoint."""

    def test_set_override_creates_record(
        self, auth_teacher, course, assignment, enrolled, student_a
    ):
        """Teacher can create a new grade override via PUT."""
        resp = auth_teacher.put(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": student_a.id, "assignmentID": assignment.id, "overrideScore": 8.5},
        )
        assert resp.status_code == 200

        override = GradeOverride.query.filter_by(
            studentID=student_a.id, assignmentID=assignment.id
        ).first()
        assert override is not None
        assert override.override_score == 8.5

    def test_set_override_updates_existing(
        self, auth_teacher, db, course, assignment, enrolled, student_a, teacher
    ):
        """PUT on an existing override updates the score rather than creating a duplicate."""
        override = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=7.0,
            teacherID=teacher.id,
        )
        db.session.add(override)
        db.session.commit()

        resp = auth_teacher.put(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": student_a.id, "assignmentID": assignment.id, "overrideScore": 9.0},
        )
        assert resp.status_code == 200

        updated = GradeOverride.query.filter_by(
            studentID=student_a.id, assignmentID=assignment.id
        ).first()
        assert updated.override_score == 9.0

    def test_set_override_teacher_only(self, auth_student, course, assignment, enrolled, student_a):
        """Students cannot set grade overrides."""
        resp = auth_student.put(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": student_a.id, "assignmentID": assignment.id, "overrideScore": 8.0},
        )
        assert resp.status_code == 403

    def test_set_override_validates_student_enrolled(
        self, auth_teacher, db, course, assignment
    ):
        """Cannot override a student who is not enrolled in the course."""
        outsider = User(
            name="Outsider",
            email="gb_outsider@test.com",
            hash_pass=generate_password_hash("password123"),
            role="student",
        )
        db.session.add(outsider)
        db.session.commit()

        resp = auth_teacher.put(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": outsider.id, "assignmentID": assignment.id, "overrideScore": 8.0},
        )
        assert resp.status_code == 404

    def test_set_override_validates_assignment_in_course(
        self, auth_teacher, db, course, enrolled, student_a, teacher
    ):
        """Cannot override with an assignment that belongs to a different course."""
        other_course = Course(teacherID=teacher.id, name="Other Course")
        db.session.add(other_course)
        db.session.flush()
        other_assignment = Assignment(courseID=other_course.id, name="Other HW")
        db.session.add(other_assignment)
        db.session.commit()

        resp = auth_teacher.put(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": student_a.id, "assignmentID": other_assignment.id, "overrideScore": 8.0},
        )
        assert resp.status_code == 404


# ============================================================================
# DELETE /gradebook/course/<id>/override — CLEAR GRADE OVERRIDE
# ============================================================================


class TestClearOverride:
    """Tests for the clear grade override endpoint."""

    def test_clear_override_deletes_record(
        self, auth_teacher, db, course, assignment, enrolled, student_a, teacher
    ):
        """Teacher can delete an existing override."""
        override = GradeOverride(
            studentID=student_a.id,
            assignmentID=assignment.id,
            courseID=course.id,
            override_score=8.0,
            teacherID=teacher.id,
        )
        db.session.add(override)
        db.session.commit()

        resp = auth_teacher.delete(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": student_a.id, "assignmentID": assignment.id},
        )
        assert resp.status_code == 200

        assert GradeOverride.query.filter_by(
            studentID=student_a.id, assignmentID=assignment.id
        ).first() is None

    def test_clear_override_nonexistent(
        self, auth_teacher, course, assignment, enrolled, student_a
    ):
        """Clearing a nonexistent override returns 404."""
        resp = auth_teacher.delete(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": student_a.id, "assignmentID": assignment.id},
        )
        assert resp.status_code == 404

    def test_clear_override_teacher_only(
        self, auth_student, course, assignment, enrolled, student_a
    ):
        """Students cannot clear grade overrides."""
        resp = auth_student.delete(
            f"/gradebook/course/{course.id}/override",
            json={"studentID": student_a.id, "assignmentID": assignment.id},
        )
        assert resp.status_code == 403


# ============================================================================
# GET /gradebook/course/<id>/reviews — STUDENT+ASSIGNMENT REVIEWS
# ============================================================================


class TestGetStudentReviews:
    """Tests for the student+assignment review detail endpoint."""

    def test_get_reviews_for_student_assignment(
        self, auth_teacher, course, assignment, enrolled, reviews_for_alice, student_a
    ):
        """Returns individual reviews with comments and criteria."""
        resp = auth_teacher.get(
            f"/gradebook/course/{course.id}/reviews",
            query_string={"studentID": student_a.id, "assignmentID": assignment.id},
        )
        assert resp.status_code == 200
        data = resp.json
        assert "individualReviews" in data
        assert "groupReviews" in data
        assert len(data["individualReviews"]) == 1
        assert data["individualReviews"][0]["comments"] == "Good work"

    def test_get_reviews_includes_group_reviews(
        self, auth_teacher, db, course, assignment, enrolled,
        student_a, student_b, group_setup
    ):
        """Group reviews for the student's group are included in the response."""
        group_a, group_b, rubric, criteria = group_setup

        # Student B (in group Beta) reviews group Alpha
        review = Review(
            assignmentID=assignment.id,
            reviewerID=student_b.id,
            revieweeID=group_a.id,
            review_type="group",
            comments="Nice teamwork",
        )
        db.session.add(review)
        db.session.flush()
        db.session.add(Criterion(reviewID=review.id, criterionRowID=criteria[0].id, grade=8))
        db.session.commit()

        resp = auth_teacher.get(
            f"/gradebook/course/{course.id}/reviews",
            query_string={"studentID": student_a.id, "assignmentID": assignment.id},
        )
        assert resp.status_code == 200
        assert len(resp.json["groupReviews"]) == 1
        assert resp.json["groupReviews"][0]["comments"] == "Nice teamwork"

    def test_get_reviews_teacher_only(self, auth_student, course, assignment, enrolled, student_a):
        """Students cannot access the review detail endpoint."""
        resp = auth_student.get(
            f"/gradebook/course/{course.id}/reviews",
            query_string={"studentID": student_a.id, "assignmentID": assignment.id},
        )
        assert resp.status_code == 403
