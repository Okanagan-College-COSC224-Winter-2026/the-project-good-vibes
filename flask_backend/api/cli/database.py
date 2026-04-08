import os

import click
from flask.cli import with_appcontext
from sqlalchemy import inspect, text
from werkzeug.security import generate_password_hash

from ..models import User, Course, Assignment, AssignmentResource
from ..models.db import db


@click.command("migrate_assignment_columns")
@with_appcontext
def migrate_assignment_columns_command():
    """Add missing Assignment columns for existing databases.

    This command is idempotent and safe to run multiple times.
    """

    inspector = inspect(db.engine)
    if not inspector.has_table("Assignment"):
        click.echo("Assignment table does not exist. Run 'flask init_db' first.", err=True)
        return

    existing_columns = {column["name"] for column in inspector.get_columns("Assignment")}
    migrations = [
        ("description", 'ALTER TABLE "Assignment" ADD COLUMN description TEXT'),
        ("start_date", 'ALTER TABLE "Assignment" ADD COLUMN start_date TIMESTAMP'),
        ("due_date", 'ALTER TABLE "Assignment" ADD COLUMN due_date TIMESTAMP'),
        ("is_anonymous", 'ALTER TABLE "Assignment" ADD COLUMN is_anonymous BOOLEAN DEFAULT TRUE'),
        ("individual_reviews", 'ALTER TABLE "Assignment" ADD COLUMN individual_reviews BOOLEAN DEFAULT TRUE'),
        ("group_reviews", 'ALTER TABLE "Assignment" ADD COLUMN group_reviews BOOLEAN DEFAULT TRUE'),
    ]

    applied = 0
    for column_name, statement in migrations:
        if column_name in existing_columns:
            click.echo(f"Column '{column_name}' already exists on Assignment")
            continue
        db.session.execute(text(statement))
        applied += 1
        click.echo(f"Added column '{column_name}' to Assignment")

    if applied:
        db.session.commit()
        click.echo(f"Assignment migration completed ({applied} column(s) added)")
    else:
        click.echo("Assignment migration completed (no changes needed)")


@click.command("migrate_assignment_resources")
@with_appcontext
def migrate_assignment_resources_command():
    """Create AssignmentResource table if missing (idempotent)."""

    inspector = inspect(db.engine)
    if inspector.has_table("AssignmentResource"):
        click.echo("AssignmentResource table already exists")
        return

    AssignmentResource.__table__.create(bind=db.engine, checkfirst=True)
    click.echo("AssignmentResource table created")


@click.command("init_db")
@with_appcontext
def init_db_command():
    """Initialize the database"""
    db.create_all()
    click.echo("Database is created")


@click.command("drop_db")
@with_appcontext
def drop_db_command():
    """Drop all database tables"""
    if click.confirm("Are you sure you want to drop all tables?"):
        db.drop_all()
        click.echo("Database tables dropped")


@click.command("add_users")
@with_appcontext
def add_users_command():
    """Add sample users to the database"""
    # Create mock users that match the User model: (name, email, hash_pass, role)
    sample_users = [
        {
            "name": "Example Student",
            "email": "student@example.com",
            "password": "123456",
            "role": "student",
        },
        {
            "name": "Example Teacher",
            "email": "teacher@example.com",
            "password": "123456",
            "role": "teacher",
        },
        {
            "name": "Example Admin",
            "email": "admin@example.com",
            "password": "123456",
            "role": "admin",
        },
    ]

    for u in sample_users:
        # check existence by email
        if not User.get_by_email(u["email"]):
            hashed = generate_password_hash(u["password"], method="pbkdf2:sha256")
            user = User(name=u["name"], email=u["email"], hash_pass=hashed, role=u["role"])
            User.create_user(user)
            click.echo(f"User '{user.email}' created (role={user.role})")
        else:
            click.echo(f"User '{u['email']}' already exists")


@click.command("create_admin")
@with_appcontext
def create_admin_command():
    """Create an admin user"""
    name = click.prompt("Admin name")
    email = click.prompt("Admin email")
    password = click.prompt("Password", hide_input=True, confirmation_prompt=True)

    # Check if user already exists
    if User.get_by_email(email):
        click.echo(f"Error: User with email '{email}' already exists", err=True)
        return

    # Create admin user
    hashed = generate_password_hash(password, method="pbkdf2:sha256")
    admin = User(name=name, email=email, hash_pass=hashed, role="admin")
    User.create_user(admin)
    click.echo(f"Admin user '{email}' created successfully")


@click.command("ensure_admin")
@with_appcontext
def ensure_admin_command():
    """Ensure a default admin exists using environment variables.

    Requires DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_EMAIL, DEFAULT_ADMIN_PASSWORD.
    Safe to run repeatedly; updates role/password if the user already exists.
    """

    name = os.environ.get("DEFAULT_ADMIN_NAME")
    email = os.environ.get("DEFAULT_ADMIN_EMAIL")
    password = os.environ.get("DEFAULT_ADMIN_PASSWORD")

    if not all([name, email, password]):
        click.echo(
            "DEFAULT_ADMIN_* environment variables not fully set; skipping admin bootstrap"
        )
        return

    assert name is not None
    assert email is not None
    assert password is not None

    existing_user = User.get_by_email(email)
    hashed = generate_password_hash(password, method="pbkdf2:sha256")

    if existing_user:
        if existing_user.role != "admin" or existing_user.hash_pass != hashed:
            existing_user.role = "admin"
            existing_user.hash_pass = hashed
            existing_user.update()
            click.echo(f"Updated existing user '{email}' to admin role")
        else:
            click.echo(f"Admin user '{email}' already exists; no changes made")
        return

    admin = User(name=name, email=email, hash_pass=hashed, role="admin")
    User.create_user(admin)
    click.echo(f"Admin user '{email}' created successfully")


@click.command("add_sample_courses")
@with_appcontext
def add_sample_courses_command():
    """Add sample courses and assignments to the database"""
    # Get the teacher user (or create one if it doesn't exist)
    teacher = User.get_by_email("teacher@example.com")
    if not teacher:
        click.echo("Error: Teacher user 'teacher@example.com' not found. Run 'flask add_users' first.", err=True)
        return

    # Define sample courses
    sample_courses = [
        {"name": "COSC 404 Advanced Database Management Systems"},
        {"name": "COSC 470 Software Engineering"},
        {"name": "COSC 360 Server Platform As A Service"},
    ]

    for course_data in sample_courses:
        # Check if course already exists
        existing_course = Course.get_by_name_teacher(course_data["name"], teacher.id)
        if existing_course:
            click.echo(f"Course '{course_data['name']}' already exists")
            continue

        # Create course
        course = Course(teacherID=teacher.id, name=course_data["name"])
        Course.create_course(course)
        click.echo(f"Course '{course.name}' created (id={course.id})")

        # Add an example assignment to the course
        assignment = Assignment(
            courseID=course.id,
            name="Example Assignment",
            rubric_text="Example rubric",
            # description=None,
            # start_date=None,
            # due_date=None,
        )
        Assignment.create(assignment)
        click.echo(f"  - Assignment 'Example Assignment' added to '{course.name}'")

    click.echo("Sample courses and assignments created successfully")


@click.command("migrate_review_comments")
@with_appcontext
def migrate_review_comments_command():
    """Add comments column to Review table for existing databases.

    This command is idempotent and safe to run multiple times.
    """
    inspector = inspect(db.engine)
    if not inspector.has_table("Review"):
        click.echo("Review table does not exist. Run 'flask init_db' first.", err=True)
        return

    existing_columns = {column["name"] for column in inspector.get_columns("Review")}
    if "comments" in existing_columns:
        click.echo("Column 'comments' already exists on Review")
        return

    db.session.execute(text('ALTER TABLE "Review" ADD COLUMN comments VARCHAR(500)'))
    db.session.commit()
    click.echo("Added column 'comments' to Review")


@click.command("migrate_course_image")
@with_appcontext
def migrate_course_image_command():
    """Add image_path column to Course table for existing databases (idempotent)."""
    inspector = inspect(db.engine)
    if not inspector.has_table("Course"):
        click.echo("Course table does not exist. Run 'flask init_db' first.", err=True)
        return

    existing_columns = {col["name"] for col in inspector.get_columns("Course")}
    if "image_path" in existing_columns:
        click.echo("Column 'image_path' already exists on Course — no changes needed.")
        return

    db.session.execute(text('ALTER TABLE "Course" ADD COLUMN image_path VARCHAR(255)'))
    db.session.commit()
    click.echo("Added column 'image_path' to Course table.")


def init_app(app):
    """Register CLI commands with the Flask app"""
    from .seed_demo import seed_demo_command
    app.cli.add_command(seed_demo_command)
    app.cli.add_command(init_db_command)
    app.cli.add_command(drop_db_command)
    app.cli.add_command(migrate_assignment_columns_command)
    app.cli.add_command(migrate_assignment_resources_command)
    app.cli.add_command(add_users_command)
    app.cli.add_command(create_admin_command)
    app.cli.add_command(ensure_admin_command)
    app.cli.add_command(add_sample_courses_command)
    app.cli.add_command(migrate_course_image_command)
    app.cli.add_command(migrate_review_comments_command)
    app.cli.add_command(migrate_group_reviews_command)
    app.cli.add_command(migrate_user_avatar_command)


@click.command("migrate_group_reviews")
@with_appcontext
def migrate_group_reviews_command():
    """Add review_type column to Review and rubric_type column to Rubric.

    Needed for group-review support. Existing rows default to 'individual'.
    This command is idempotent and safe to run multiple times.
    """
    inspector = inspect(db.engine)
    applied = 0

    # --- Review table ---
    if not inspector.has_table("Review"):
        click.echo("Review table does not exist. Run 'flask init_db' first.", err=True)
        return

    review_cols = {col["name"] for col in inspector.get_columns("Review")}
    if "review_type" in review_cols:
        click.echo("Column 'review_type' already exists on Review")
    else:
        db.session.execute(
            text('ALTER TABLE "Review" ADD COLUMN review_type VARCHAR(20) NOT NULL DEFAULT \'individual\'')
        )
        applied += 1
        click.echo("Added column 'review_type' to Review (default='individual')")

    # --- Rubric table ---
    if not inspector.has_table("Rubric"):
        click.echo("Rubric table does not exist. Run 'flask init_db' first.", err=True)
        return

    rubric_cols = {col["name"] for col in inspector.get_columns("Rubric")}
    if "rubric_type" in rubric_cols:
        click.echo("Column 'rubric_type' already exists on Rubric")
    else:
        db.session.execute(
            text('ALTER TABLE "Rubric" ADD COLUMN rubric_type VARCHAR(20) NOT NULL DEFAULT \'individual\'')
        )
        applied += 1
        click.echo("Added column 'rubric_type' to Rubric (default='individual')")

    if applied:
        db.session.commit()
        click.echo(f"Group reviews migration completed ({applied} column(s) added)")
    else:
        click.echo("Group reviews migration completed (no changes needed)")


@click.command("migrate_user_avatar")
@with_appcontext
def migrate_user_avatar_command():
    """Add avatar_path column to User table for existing databases (idempotent)."""

    inspector = inspect(db.engine)
    if not inspector.has_table("User"):
        click.echo("User table does not exist. Run 'flask init_db' first.", err=True)
        return

    existing_columns = {col["name"] for col in inspector.get_columns("User")}
    if "avatar_path" in existing_columns:
        click.echo("Column 'avatar_path' already exists on User — no changes needed.")
        return

    db.session.execute(text('ALTER TABLE "User" ADD COLUMN avatar_path VARCHAR(255)'))
    db.session.commit()
    click.echo("Added column 'avatar_path' to User table.")
