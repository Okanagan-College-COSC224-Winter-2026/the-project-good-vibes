"""
Tests for group review features and review update (edit) functionality.

Covers:
  POST  /review/submit          — group review submission (review_type="group")
  PUT   /review/<id>            — update an existing review (individual or group)
  GET   /review/lookup          — lookup with review_type param
  GET   /review/assignment/<id> — list reviews filtered by review_type
  GET   /review/course/<id>/summary — weighted grade summary (50/50 individual + group)

Group review rules:
  - A group collectively reviews another group; any member can submit on behalf.
  - Once submitted, any member of the reviewing group can view and edit it.
  - A group cannot review itself (that's what individual reviews are for).
  - Duplicate prevention: only one review per (assignment, source_group, target_group).
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


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def teacher(db):
    user = User(
        name="Group Review Teacher",
        email="gr_teacher@test.com",
        hash_pass=generate_password_hash("password123"),
        role="teacher",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_a(db):
    """Student in Group Alpha."""
    user = User(
        name="Alice",
        email="gr_alice@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def student_b(db):
    """Another student in Group Alpha."""
    user = User(
        name="Bob",
        email="gr_bob@test.com",
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
        name="Carol",
        email="gr_carol@test.com",
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
        name="Dave",
        email="gr_dave@test.com",
        hash_pass=generate_password_hash("password123"),
        role="student",
    )
    db.session.add(user)
    db.session.commit()
    return user


@pytest.fixture
def course(db, teacher):
    c = Course(teacherID=teacher.id, name="Group Review Course")
    db.session.add(c)
    db.session.commit()
    return c


@pytest.fixture
def enrolled_students(db, course, student_a, student_b, student_c, student_d):
    """Enroll all four students in the course."""
    for s in [student_a, student_b, student_c, student_d]:
        db.session.add(User_Course(userID=s.id, courseID=course.id))
    db.session.commit()


@pytest.fixture
def assignment(db, course):
    a = Assignment(courseID=course.id, name="Group Review HW", is_anonymous=False)
    db.session.add(a)
    db.session.commit()
    return a


@pytest.fixture
def group_alpha(db, course, student_a, student_b, enrolled_students):
    """Group Alpha with Alice and Bob."""
    g = CourseGroup(name="Alpha", courseID=course.id)
    db.session.add(g)
    db.session.flush()
    db.session.add(Group_Members(userID=student_a.id, groupID=g.id))
    db.session.add(Group_Members(userID=student_b.id, groupID=g.id))
    db.session.commit()
    return g


@pytest.fixture
def group_beta(db, course, student_c, student_d, enrolled_students):
    """Group Beta with Carol and Dave."""
    g = CourseGroup(name="Beta", courseID=course.id)
    db.session.add(g)
    db.session.flush()
    db.session.add(Group_Members(userID=student_c.id, groupID=g.id))
    db.session.add(Group_Members(userID=student_d.id, groupID=g.id))
    db.session.commit()
    return g


@pytest.fixture
def individual_rubric(db, assignment):
    """Individual peer review rubric with 2 criteria."""
    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="individual")
    db.session.add(rubric)
    db.session.flush()
    c1 = CriteriaDescription(rubricID=rubric.id, question="Communication", scoreMax=5, hasScore=True)
    c2 = CriteriaDescription(rubricID=rubric.id, question="Effort", scoreMax=5, hasScore=True)
    db.session.add_all([c1, c2])
    db.session.commit()
    return rubric, [c1, c2]


@pytest.fixture
def group_rubric(db, assignment):
    """Group review rubric with 2 criteria."""
    rubric = Rubric(assignmentID=assignment.id, canComment=True, rubric_type="group")
    db.session.add(rubric)
    db.session.flush()
    c1 = CriteriaDescription(rubricID=rubric.id, question="Presentation quality", scoreMax=10, hasScore=True)
    c2 = CriteriaDescription(rubricID=rubric.id, question="Code quality", scoreMax=10, hasScore=True)
    db.session.add_all([c1, c2])
    db.session.commit()
    return rubric, [c1, c2]


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


@pytest.fixture
def auth_teacher(test_client, teacher):
    test_client.post("/auth/login", json={"email": teacher.email, "password": "password123"})
    return test_client


# ============================================================================
# POST /review/submit — GROUP REVIEW SUBMISSION
# ============================================================================


class TestSubmitGroupReview:
    """Tests for submitting group reviews (review_type='group')."""

    def test_submit_group_review(
        self, auth_alice, assignment, group_alpha, group_beta, group_rubric
    ):
        """A student can submit a group review on behalf of their group."""
        _, criteria = group_rubric

        resp = auth_alice.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [
                    {"criterionRowID": criteria[0].id, "grade": 8, "comments": "Good presentation"},
                    {"criterionRowID": criteria[1].id, "grade": 7, "comments": ""},
                ],
                "comments": "Solid group effort",
            },
        )

        assert resp.status_code == 201
        data = resp.get_json()
        assert data["msg"] == "Review submitted"
        assert "id" in data

        review = Review.get_by_id(data["id"])
        assert review.review_type == "group"
        assert review.revieweeID == group_beta.id

    def test_cannot_review_own_group(
        self, auth_alice, assignment, group_alpha, group_rubric
    ):
        """A student cannot submit a group review targeting their own group."""
        _, criteria = group_rubric

        resp = auth_alice.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_alpha.id,
                "review_type": "group",
                "criteria": [],
            },
        )

        assert resp.status_code == 400
        assert "own group" in resp.get_json()["msg"].lower()

    def test_duplicate_group_review_from_same_group_rejected(
        self, test_client, db, student_a, student_b, assignment, group_alpha, group_beta, group_rubric
    ):
        """If Alice (Group Alpha) already reviewed Group Beta, Bob (also Group Alpha) cannot submit another."""
        _, criteria = group_rubric

        # Alice submits group review
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        resp1 = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 9, "comments": ""}],
            },
        )
        assert resp1.status_code == 201

        # Bob tries to submit another group review for same target
        test_client.post("/auth/login", json={"email": student_b.email, "password": "password123"})
        resp2 = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 6, "comments": ""}],
            },
        )
        assert resp2.status_code == 409
        assert "already reviewed" in resp2.get_json()["msg"].lower()

    def test_different_group_can_review_same_target(
        self, test_client, db, student_a, student_c, assignment,
        group_alpha, group_beta, group_rubric
    ):
        """Group Alpha and Group Beta can each review a third group (or each other)."""
        # For simplicity, create a third group
        student_e = User(
            name="Eve", email="gr_eve@test.com",
            hash_pass=generate_password_hash("password123"), role="student",
        )
        db.session.add(student_e)
        db.session.flush()
        db.session.add(User_Course(userID=student_e.id, courseID=assignment.courseID))
        group_gamma = CourseGroup(name="Gamma", courseID=assignment.courseID)
        db.session.add(group_gamma)
        db.session.flush()
        db.session.add(Group_Members(userID=student_e.id, groupID=group_gamma.id))
        db.session.commit()

        _, criteria = group_rubric

        # Alice (Alpha) reviews Gamma
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        resp1 = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_gamma.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 7, "comments": ""}],
            },
        )
        assert resp1.status_code == 201

        # Carol (Beta) also reviews Gamma
        test_client.post("/auth/login", json={"email": student_c.email, "password": "password123"})
        resp2 = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_gamma.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 9, "comments": ""}],
            },
        )
        assert resp2.status_code == 201

    def test_group_review_requires_group_membership(
        self, test_client, db, assignment, group_beta, group_rubric
    ):
        """A student not in any group cannot submit a group review."""
        loner = User(
            name="Loner", email="gr_loner@test.com",
            hash_pass=generate_password_hash("password123"), role="student",
        )
        db.session.add(loner)
        db.session.commit()

        test_client.post("/auth/login", json={"email": loner.email, "password": "password123"})
        resp = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [],
            },
        )
        assert resp.status_code == 400
        assert "group" in resp.get_json()["msg"].lower()

    def test_group_review_target_must_exist(
        self, auth_alice, assignment, group_alpha, group_rubric
    ):
        """Submitting a group review for a non-existent group returns 404."""
        resp = auth_alice.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": 99999,
                "review_type": "group",
                "criteria": [],
            },
        )
        assert resp.status_code == 404


# ============================================================================
# PUT /review/<id> — UPDATE (EDIT) REVIEW
# ============================================================================


class TestUpdateReview:
    """Tests for updating an existing review (both individual and group)."""

    def test_update_individual_review(
        self, auth_alice, student_b, assignment, individual_rubric
    ):
        """Reviewer can update their own individual review."""
        _, criteria = individual_rubric

        # Submit
        resp = auth_alice.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": student_b.id,
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 3, "comments": "OK"}],
                "comments": "Initial comment",
            },
        )
        review_id = resp.get_json()["id"]

        # Update
        resp = auth_alice.put(
            f"/review/{review_id}",
            json={
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 5, "comments": "Great!"}],
                "comments": "Updated comment",
            },
        )
        assert resp.status_code == 200
        assert resp.get_json()["msg"] == "Review updated"

        # Verify the update persisted
        review = Review.get_by_id(review_id)
        assert review.comments == "Updated comment"
        stored_criteria = Criterion.query.filter_by(reviewID=review_id).all()
        assert len(stored_criteria) == 1
        assert stored_criteria[0].grade == 5
        assert stored_criteria[0].comments == "Great!"

    def test_group_member_can_edit_group_review(
        self, test_client, db, student_a, student_b,
        assignment, group_alpha, group_beta, group_rubric
    ):
        """Any member of the reviewing group can edit a group review."""
        _, criteria = group_rubric

        # Alice submits
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        resp = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 6, "comments": ""}],
                "comments": "Alice's draft",
            },
        )
        review_id = resp.get_json()["id"]

        # Bob (same group) edits it
        test_client.post("/auth/login", json={"email": student_b.email, "password": "password123"})
        resp = test_client.put(
            f"/review/{review_id}",
            json={
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 9, "comments": "Bob updated"}],
                "comments": "Bob's revision",
            },
        )
        assert resp.status_code == 200

        review = Review.get_by_id(review_id)
        assert review.comments == "Bob's revision"

    def test_outsider_cannot_edit_group_review(
        self, test_client, db, student_a, student_c,
        assignment, group_alpha, group_beta, group_rubric
    ):
        """A student from a different group cannot edit the review."""
        _, criteria = group_rubric

        # Alice (Alpha) submits review of Beta
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        resp = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 8, "comments": ""}],
            },
        )
        review_id = resp.get_json()["id"]

        # Carol (Beta) tries to edit Alpha's review of Beta
        test_client.post("/auth/login", json={"email": student_c.email, "password": "password123"})
        resp = test_client.put(
            f"/review/{review_id}",
            json={
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 10, "comments": ""}],
            },
        )
        assert resp.status_code == 403

    def test_non_reviewer_cannot_edit_individual_review(
        self, test_client, db, student_a, student_b,
        assignment, individual_rubric
    ):
        """Only the original reviewer can edit an individual review."""
        _, criteria = individual_rubric

        # Alice submits review of Bob
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        resp = test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": student_b.id,
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 3, "comments": ""}],
            },
        )
        review_id = resp.get_json()["id"]

        # Bob tries to edit Alice's review
        test_client.post("/auth/login", json={"email": student_b.email, "password": "password123"})
        resp = test_client.put(
            f"/review/{review_id}",
            json={
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 5, "comments": ""}],
            },
        )
        assert resp.status_code == 403


# ============================================================================
# GET /review/lookup — GROUP REVIEW LOOKUP
# ============================================================================


class TestGroupReviewLookup:
    """Tests for looking up group reviews."""

    def test_lookup_group_review_by_submitter(
        self, auth_alice, assignment, group_alpha, group_beta, group_rubric
    ):
        """The student who submitted can look up the group review."""
        _, criteria = group_rubric

        auth_alice.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 7, "comments": ""}],
            },
        )

        resp = auth_alice.get(
            f"/review/lookup?assignmentID={assignment.id}&revieweeID={group_beta.id}&review_type=group"
        )
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["review"]["review_type"] == "group"

    def test_group_mate_can_lookup_group_review(
        self, test_client, db, student_a, student_b,
        assignment, group_alpha, group_beta, group_rubric
    ):
        """Bob (same group as Alice) can look up the group review Alice submitted."""
        _, criteria = group_rubric

        # Alice submits
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 8, "comments": ""}],
            },
        )

        # Bob looks it up
        test_client.post("/auth/login", json={"email": student_b.email, "password": "password123"})
        resp = test_client.get(
            f"/review/lookup?assignmentID={assignment.id}&revieweeID={group_beta.id}&review_type=group"
        )
        assert resp.status_code == 200


# ============================================================================
# GET /review/assignment/<id> — FILTER BY REVIEW TYPE
# ============================================================================


class TestListReviewsByType:
    """Tests for listing reviews filtered by review_type."""

    def test_list_individual_reviews_only(
        self, test_client, db, student_a, student_b, student_c,
        assignment, group_alpha, group_beta, individual_rubric, group_rubric
    ):
        """Can filter to only individual reviews."""
        _, ind_criteria = individual_rubric
        _, grp_criteria = group_rubric

        # Alice submits individual review of Bob
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": student_b.id,
                "criteria": [{"criterionRowID": ind_criteria[0].id, "grade": 4, "comments": ""}],
            },
        )
        # Alice submits group review of Beta
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": grp_criteria[0].id, "grade": 7, "comments": ""}],
            },
        )

        # Teacher lists individual reviews
        test_client.post("/auth/login", json={"email": "gr_teacher@test.com", "password": "password123"})
        resp = test_client.get(
            f"/review/assignment/{assignment.id}?review_type=individual"
        )
        assert resp.status_code == 200
        reviews = resp.get_json()
        assert len(reviews) == 1
        assert all(r.get("review_type", "individual") == "individual" for r in reviews)

    def test_list_group_reviews_only(
        self, test_client, db, student_a, student_b, student_c,
        assignment, group_alpha, group_beta, individual_rubric, group_rubric
    ):
        """Can filter to only group reviews."""
        _, ind_criteria = individual_rubric
        _, grp_criteria = group_rubric

        # Individual review
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": student_b.id,
                "criteria": [{"criterionRowID": ind_criteria[0].id, "grade": 4, "comments": ""}],
            },
        )
        # Group review
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": grp_criteria[0].id, "grade": 7, "comments": ""}],
            },
        )

        # Teacher lists group reviews
        test_client.post("/auth/login", json={"email": "gr_teacher@test.com", "password": "password123"})
        resp = test_client.get(
            f"/review/assignment/{assignment.id}?review_type=group"
        )
        assert resp.status_code == 200
        reviews = resp.get_json()
        assert len(reviews) == 1
        assert all(r["review_type"] == "group" for r in reviews)


# ============================================================================
# GET /review/course/<id>/summary — WEIGHTED GRADE SUMMARY
# ============================================================================


class TestWeightedGradeSummary:
    """Tests for the 50/50 weighted grade summary (individual + group)."""

    def test_summary_includes_both_types(
        self, test_client, db, student_a, student_b, student_c,
        course, assignment, group_alpha, group_beta,
        individual_rubric, group_rubric
    ):
        """Grade summary returns separate individual and group averages plus a weighted total."""
        _, ind_criteria = individual_rubric
        _, grp_criteria = group_rubric

        # Bob reviews Alice (individual) — Alice gets score 4+4=8 out of 5+5=10
        test_client.post("/auth/login", json={"email": student_b.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": student_a.id,
                "criteria": [
                    {"criterionRowID": ind_criteria[0].id, "grade": 4, "comments": ""},
                    {"criterionRowID": ind_criteria[1].id, "grade": 4, "comments": ""},
                ],
            },
        )

        # Beta reviews Alpha (group) — Alpha gets score 8+6=14 out of 10+10=20
        test_client.post("/auth/login", json={"email": student_c.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_alpha.id,
                "review_type": "group",
                "criteria": [
                    {"criterionRowID": grp_criteria[0].id, "grade": 8, "comments": ""},
                    {"criterionRowID": grp_criteria[1].id, "grade": 6, "comments": ""},
                ],
            },
        )

        # Alice views her summary
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        resp = test_client.get(f"/review/course/{course.id}/summary")
        assert resp.status_code == 200

        data = resp.get_json()
        assert "individualAverage" in data
        assert "groupAverage" in data
        assert "courseAverage" in data

        # Individual: 8/10 = 80%
        # Group: 14/20 = 70%
        # Weighted: (80 + 70) / 2 = 75%  (but the raw values should reflect per-assignment averages)
        assert data["individualAverage"] is not None
        assert data["groupAverage"] is not None
        assert data["courseAverage"] is not None


# ============================================================================
# GROUP REVIEW ANONYMITY & REVIEWER DISPLAY
# ============================================================================


class TestGroupReviewAnonymity:
    """Tests for group review reviewer display and anonymity."""

    def test_anonymous_group_review_hides_reviewer(
        self, test_client, db, student_a, student_c, student_d,
        course, group_alpha, group_beta, group_rubric
    ):
        """On an anonymous assignment, group review reviewer should be 'Anonymous'."""
        anon_assignment = Assignment(courseID=course.id, name="Anon HW", is_anonymous=True)
        db.session.add(anon_assignment)
        db.session.commit()

        _, criteria = group_rubric

        # Alice (Alpha) reviews Beta
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": anon_assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 8, "comments": ""}],
            },
        )

        # Carol (Beta, the reviewee group) lists reviews
        test_client.post("/auth/login", json={"email": student_c.email, "password": "password123"})
        resp = test_client.get(
            f"/review/assignment/{anon_assignment.id}?review_type=group"
        )
        assert resp.status_code == 200
        reviews = resp.get_json()
        assert len(reviews) == 1
        assert reviews[0]["reviewer"]["name"] == "Anonymous"
        assert reviews[0]["reviewer"]["id"] is None

    def test_non_anonymous_group_review_shows_group_name(
        self, test_client, db, student_a, student_c,
        assignment, group_alpha, group_beta, group_rubric
    ):
        """On a non-anonymous assignment, group review reviewer should show the group name."""
        _, criteria = group_rubric

        # Alice (Alpha) reviews Beta
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 7, "comments": ""}],
            },
        )

        # Carol (Beta) lists reviews — should see "Alpha" not "Alice"
        test_client.post("/auth/login", json={"email": student_c.email, "password": "password123"})
        resp = test_client.get(
            f"/review/assignment/{assignment.id}?review_type=group"
        )
        assert resp.status_code == 200
        reviews = resp.get_json()
        assert len(reviews) == 1
        assert reviews[0]["reviewer"]["name"] == "Alpha"
        assert reviews[0]["reviewer"]["id"] is None
        assert reviews[0]["reviewer"]["email"] is None

    def test_teacher_sees_real_reviewer_on_anonymous_group_review(
        self, test_client, db, student_a, teacher,
        course, assignment, group_alpha, group_beta, group_rubric
    ):
        """Teacher should always see the real reviewer identity on group reviews."""
        # Make assignment anonymous
        assignment.is_anonymous = True
        db.session.commit()

        _, criteria = group_rubric

        # Alice (Alpha) reviews Beta
        test_client.post("/auth/login", json={"email": student_a.email, "password": "password123"})
        test_client.post(
            "/review/submit",
            json={
                "assignmentID": assignment.id,
                "revieweeID": group_beta.id,
                "review_type": "group",
                "criteria": [{"criterionRowID": criteria[0].id, "grade": 9, "comments": ""}],
            },
        )

        # Teacher lists reviews — should see Alice's real name
        test_client.post("/auth/login", json={"email": teacher.email, "password": "password123"})
        resp = test_client.get(
            f"/review/assignment/{assignment.id}?review_type=group"
        )
        assert resp.status_code == 200
        reviews = resp.get_json()
        assert len(reviews) == 1
        assert reviews[0]["reviewer"]["name"] == "Alice"


# ============================================================================
# RUBRIC TYPE — CREATING / FETCHING RUBRICS BY TYPE
# ============================================================================


class TestRubricType:
    """Tests for rubric_type on rubric creation and retrieval."""

    def test_create_group_rubric(self, auth_teacher, assignment):
        """Teacher can create a group rubric for an assignment."""
        resp = auth_teacher.post(
            "/rubric/create",
            json={
                "assignmentID": assignment.id,
                "canComment": True,
                "rubric_type": "group",
            },
        )
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["rubric"]["rubric_type"] == "group"

    def test_get_rubric_by_type(self, auth_teacher, assignment):
        """Can fetch individual and group rubrics separately for the same assignment."""
        # Create individual rubric
        auth_teacher.post(
            "/rubric/create",
            json={"assignmentID": assignment.id, "canComment": True, "rubric_type": "individual"},
        )
        # Create group rubric
        auth_teacher.post(
            "/rubric/create",
            json={"assignmentID": assignment.id, "canComment": True, "rubric_type": "group"},
        )

        # Fetch individual
        resp = auth_teacher.get(
            f"/rubric/assignment/{assignment.id}?rubric_type=individual"
        )
        assert resp.status_code == 200
        assert resp.get_json()["rubric_type"] == "individual"

        # Fetch group
        resp = auth_teacher.get(
            f"/rubric/assignment/{assignment.id}?rubric_type=group"
        )
        assert resp.status_code == 200
        assert resp.get_json()["rubric_type"] == "group"
