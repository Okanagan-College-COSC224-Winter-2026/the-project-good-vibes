"""Seed a realistic demo dataset for showcasing the peer evaluation app.

Creates a teacher, students, courses, groups, assignments with rubrics,
submissions, peer reviews (individual + group), and grade overrides.

Usage:
    flask --app api seed_demo
    docker exec -it peereval-flask flask --app api seed_demo
"""

from datetime import datetime, timedelta, timezone

import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash

from ..models import (
    Assignment,
    Course,
    CourseGroup,
    CriteriaDescription,
    Criterion,
    Group_Members,
    Review,
    Rubric,
    Submission,
    User,
    User_Course,
)
from ..models.db import db
from ..models.grade_override_model import GradeOverride


def _hash(password: str) -> str:
    return generate_password_hash(password, method="pbkdf2:sha256")


def _make_user(name: str, email: str, role: str, password: str = "password") -> User:
    existing = User.get_by_email(email)
    if existing:
        return existing
    user = User(name=name, email=email, hash_pass=_hash(password), role=role)
    db.session.add(user)
    db.session.flush()
    return user


def _enroll(user: User, course: Course) -> None:
    existing = User_Course.query.filter_by(userID=user.id, courseID=course.id).first()
    if not existing:
        db.session.add(User_Course(userID=user.id, courseID=course.id))


def _add_to_group(user: User, group: CourseGroup) -> None:
    existing = Group_Members.query.filter_by(userID=user.id, groupID=group.id).first()
    if not existing:
        db.session.add(Group_Members(userID=user.id, groupID=group.id))


@click.command("seed_demo")
@with_appcontext
def seed_demo_command():
    """Seed a realistic demo dataset with courses, students, reviews, and grades."""

    click.echo("Seeding demo data...")

    # --- Users ---
    teacher = _make_user("Dr. Sarah Mitchell", "teacher@demo.com", "teacher")
    admin = _make_user("Admin", "admin@demo.com", "admin")

    students = []
    student_info = [
        ("Alice Chen", "alice@demo.com"),
        ("Bob Martinez", "bob@demo.com"),
        ("Carol Williams", "carol@demo.com"),
        ("David Kim", "david@demo.com"),
        ("Emma Johnson", "emma@demo.com"),
        ("Frank Brown", "frank@demo.com"),
    ]
    for name, email in student_info:
        students.append(_make_user(name, email, "student"))

    db.session.flush()

    # --- Courses ---
    course1 = Course.get_by_name_teacher("Software Engineering", teacher.id)
    if not course1:
        course1 = Course(teacherID=teacher.id, name="Software Engineering")
        db.session.add(course1)
        db.session.flush()

    course2 = Course.get_by_name_teacher("Database Systems", teacher.id)
    if not course2:
        course2 = Course(teacherID=teacher.id, name="Database Systems")
        db.session.add(course2)
        db.session.flush()

    # Enroll all students in both courses
    for s in students:
        _enroll(s, course1)
        _enroll(s, course2)
    db.session.flush()

    # --- Groups (Course 1) ---
    group_alpha = CourseGroup.query.filter_by(name="Alpha", courseID=course1.id).first()
    if not group_alpha:
        group_alpha = CourseGroup(name="Alpha", courseID=course1.id)
        db.session.add(group_alpha)
        db.session.flush()

    group_beta = CourseGroup.query.filter_by(name="Beta", courseID=course1.id).first()
    if not group_beta:
        group_beta = CourseGroup(name="Beta", courseID=course1.id)
        db.session.add(group_beta)
        db.session.flush()

    # Alice, Bob, Carol -> Alpha; David, Emma, Frank -> Beta
    for s in students[:3]:
        _add_to_group(s, group_alpha)
    for s in students[3:]:
        _add_to_group(s, group_beta)
    db.session.flush()

    # --- Assignment 1: "Sprint 1 Review" (Course 1, past due, individual + group) ---
    now = datetime.now(timezone.utc)
    a1 = Assignment.query.filter_by(courseID=course1.id, name="Sprint 1 Review").first()
    if not a1:
        a1 = Assignment(
            courseID=course1.id,
            name="Sprint 1 Review",
            description="Evaluate your teammates' contributions to Sprint 1.",
            due_date=now - timedelta(days=7),
            is_anonymous=True,
            individual_reviews=True,
            group_reviews=True,
        )
        db.session.add(a1)
        db.session.flush()

    # --- Assignment 2: "Sprint 2 Review" (Course 1, upcoming) ---
    a2 = Assignment.query.filter_by(courseID=course1.id, name="Sprint 2 Review").first()
    if not a2:
        a2 = Assignment(
            courseID=course1.id,
            name="Sprint 2 Review",
            description="Evaluate your teammates' contributions to Sprint 2.",
            due_date=now + timedelta(days=14),
            is_anonymous=True,
            individual_reviews=True,
            group_reviews=True,
        )
        db.session.add(a2)
        db.session.flush()

    # --- Assignment 3: "ER Diagram Peer Review" (Course 2, past due, individual only) ---
    a3 = Assignment.query.filter_by(courseID=course2.id, name="ER Diagram Peer Review").first()
    if not a3:
        a3 = Assignment(
            courseID=course2.id,
            name="ER Diagram Peer Review",
            description="Review a classmate's ER diagram for correctness and clarity.",
            due_date=now - timedelta(days=3),
            is_anonymous=False,
            individual_reviews=True,
            group_reviews=False,
        )
        db.session.add(a3)
        db.session.flush()

    # --- Rubrics for Assignment 1 ---
    ind_rubric1 = Rubric.query.filter_by(assignmentID=a1.id, rubric_type="individual").first()
    if not ind_rubric1:
        ind_rubric1 = Rubric(assignmentID=a1.id, canComment=True, rubric_type="individual")
        db.session.add(ind_rubric1)
        db.session.flush()
        db.session.add(CriteriaDescription(rubricID=ind_rubric1.id, question="Code Quality", scoreMax=10, hasScore=True))
        db.session.add(CriteriaDescription(rubricID=ind_rubric1.id, question="Communication", scoreMax=10, hasScore=True))
        db.session.add(CriteriaDescription(rubricID=ind_rubric1.id, question="Reliability", scoreMax=5, hasScore=True))
        db.session.flush()

    grp_rubric1 = Rubric.query.filter_by(assignmentID=a1.id, rubric_type="group").first()
    if not grp_rubric1:
        grp_rubric1 = Rubric(assignmentID=a1.id, canComment=True, rubric_type="group")
        db.session.add(grp_rubric1)
        db.session.flush()
        db.session.add(CriteriaDescription(rubricID=grp_rubric1.id, question="Teamwork", scoreMax=10, hasScore=True))
        db.session.add(CriteriaDescription(rubricID=grp_rubric1.id, question="Deliverable Quality", scoreMax=10, hasScore=True))
        db.session.flush()

    # --- Rubric for Assignment 3 ---
    ind_rubric3 = Rubric.query.filter_by(assignmentID=a3.id, rubric_type="individual").first()
    if not ind_rubric3:
        ind_rubric3 = Rubric(assignmentID=a3.id, canComment=True, rubric_type="individual")
        db.session.add(ind_rubric3)
        db.session.flush()
        db.session.add(CriteriaDescription(rubricID=ind_rubric3.id, question="Correctness", scoreMax=10, hasScore=True))
        db.session.add(CriteriaDescription(rubricID=ind_rubric3.id, question="Clarity", scoreMax=5, hasScore=True))
        db.session.add(CriteriaDescription(rubricID=ind_rubric3.id, question="Normalization", scoreMax=5, hasScore=True))
        db.session.flush()

    # --- Submissions for Assignment 1 (all students submitted) ---
    for s in students:
        existing = Submission.query.filter_by(assignmentID=a1.id, studentID=s.id).first()
        if not existing:
            db.session.add(Submission(assignmentID=a1.id, studentID=s.id, path=f"/demo/a1_{s.id}.pdf"))

    # Submissions for Assignment 3 (first 4 students submitted)
    for s in students[:4]:
        existing = Submission.query.filter_by(assignmentID=a3.id, studentID=s.id).first()
        if not existing:
            db.session.add(Submission(assignmentID=a3.id, studentID=s.id, path=f"/demo/a3_{s.id}.pdf"))

    db.session.flush()

    # --- Individual Reviews for Assignment 1 ---
    ind_criteria1 = CriteriaDescription.query.filter_by(rubricID=ind_rubric1.id).all()
    grp_criteria1 = CriteriaDescription.query.filter_by(rubricID=grp_rubric1.id).all()
    ind_criteria3 = CriteriaDescription.query.filter_by(rubricID=ind_rubric3.id).all()

    # Score presets for variety (per reviewer→reviewee pair)
    ind_scores = {
        # (reviewer_idx, reviewee_idx): [score1, score2, score3]
        (1, 0): [8, 9, 4],   # Bob reviews Alice
        (2, 0): [9, 8, 5],   # Carol reviews Alice
        (0, 1): [7, 6, 3],   # Alice reviews Bob
        (2, 1): [6, 7, 4],   # Carol reviews Bob
        (0, 2): [9, 9, 5],   # Alice reviews Carol
        (1, 2): [8, 8, 4],   # Bob reviews Carol
        (4, 3): [7, 8, 4],   # Emma reviews David
        (5, 3): [6, 7, 3],   # Frank reviews David
        (3, 4): [10, 9, 5],  # David reviews Emma
        (5, 4): [9, 8, 5],   # Frank reviews Emma
        (3, 5): [8, 7, 4],   # David reviews Frank
        (4, 5): [7, 7, 3],   # Emma reviews Frank
    }

    for (ri, ei), scores in ind_scores.items():
        reviewer = students[ri]
        reviewee = students[ei]
        existing = Review.query.filter_by(
            assignmentID=a1.id, reviewerID=reviewer.id, revieweeID=reviewee.id, review_type="individual"
        ).first()
        if not existing:
            review = Review(
                assignmentID=a1.id,
                reviewerID=reviewer.id,
                revieweeID=reviewee.id,
                review_type="individual",
                comments=f"Good work on Sprint 1, {reviewee.name.split()[0]}!",
            )
            db.session.add(review)
            db.session.flush()
            for crit, score in zip(ind_criteria1, scores):
                db.session.add(Criterion(reviewID=review.id, criterionRowID=crit.id, grade=score))

    # --- Group Reviews for Assignment 1 ---
    # Alpha reviews Beta and vice versa
    grp_review_scores = {
        # (reviewer_idx, reviewee_group): [score1, score2]
        (0, "beta"): [8, 7],   # Alice reviews Beta
        (1, "beta"): [7, 8],   # Bob reviews Beta
        (2, "beta"): [9, 8],   # Carol reviews Beta
        (3, "alpha"): [8, 9],  # David reviews Alpha
        (4, "alpha"): [9, 9],  # Emma reviews Alpha
        (5, "alpha"): [7, 8],  # Frank reviews Alpha
    }

    for (ri, target_group_name), scores in grp_review_scores.items():
        reviewer = students[ri]
        target_group = group_alpha if target_group_name == "alpha" else group_beta
        existing = Review.query.filter_by(
            assignmentID=a1.id, reviewerID=reviewer.id, revieweeID=target_group.id, review_type="group"
        ).first()
        if not existing:
            review = Review(
                assignmentID=a1.id,
                reviewerID=reviewer.id,
                revieweeID=target_group.id,
                review_type="group",
                comments=f"Team {target_group.name} did a solid job on their deliverable.",
            )
            db.session.add(review)
            db.session.flush()
            for crit, score in zip(grp_criteria1, scores):
                db.session.add(Criterion(reviewID=review.id, criterionRowID=crit.id, grade=score))

    # --- Individual Reviews for Assignment 3 ---
    a3_scores = {
        (1, 0): [9, 4, 5],   # Bob reviews Alice
        (2, 0): [8, 5, 4],   # Carol reviews Alice
        (0, 1): [7, 3, 4],   # Alice reviews Bob
        (3, 1): [6, 4, 3],   # David reviews Bob
        (0, 2): [10, 5, 5],  # Alice reviews Carol
        (3, 2): [9, 5, 4],   # David reviews Carol
        (1, 3): [8, 4, 4],   # Bob reviews David
        (2, 3): [7, 3, 3],   # Carol reviews David
    }

    for (ri, ei), scores in a3_scores.items():
        reviewer = students[ri]
        reviewee = students[ei]
        existing = Review.query.filter_by(
            assignmentID=a3.id, reviewerID=reviewer.id, revieweeID=reviewee.id, review_type="individual"
        ).first()
        if not existing:
            review = Review(
                assignmentID=a3.id,
                reviewerID=reviewer.id,
                revieweeID=reviewee.id,
                review_type="individual",
                comments=f"Nice ER diagram, {reviewee.name.split()[0]}.",
            )
            db.session.add(review)
            db.session.flush()
            for crit, score in zip(ind_criteria3, scores):
                db.session.add(Criterion(reviewID=review.id, criterionRowID=crit.id, grade=score))

    # --- Grade Override: teacher overrides Alice's grade on Assignment 1 ---
    existing_override = GradeOverride.query.filter_by(
        studentID=students[0].id, assignmentID=a1.id, courseID=course1.id
    ).first()
    if not existing_override:
        db.session.add(GradeOverride(
            studentID=students[0].id,
            assignmentID=a1.id,
            courseID=course1.id,
            override_score=92.0,
            teacherID=teacher.id,
        ))

    db.session.commit()

    click.echo("")
    click.echo("Demo data seeded successfully!")
    click.echo("")
    click.echo("Login credentials (all passwords: 'password'):")
    click.echo(f"  Teacher:  teacher@demo.com")
    click.echo(f"  Admin:    admin@demo.com")
    click.echo(f"  Students: alice@demo.com, bob@demo.com, carol@demo.com,")
    click.echo(f"            david@demo.com, emma@demo.com, frank@demo.com")
    click.echo("")
    click.echo("Courses:")
    click.echo(f"  - Software Engineering (2 assignments, groups, individual + group reviews)")
    click.echo(f"  - Database Systems (1 assignment, individual reviews only)")
    click.echo("")
    click.echo("Features demonstrated:")
    click.echo("  - Individual & group peer reviews with scores")
    click.echo("  - Grade override (Alice, Sprint 1 Review)")
    click.echo("  - Submitted vs Upcoming vs Overdue assignment badges")
    click.echo("  - Gradebook with equal-weight averaging")
