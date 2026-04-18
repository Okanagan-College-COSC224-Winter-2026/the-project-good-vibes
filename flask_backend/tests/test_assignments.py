"""
Tests for assignments endpoints
"""

import json
import datetime
from datetime import timedelta

def test_teacher_can_create_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they create a new assignment via POST /assignment
    THEN the assignment should be created successfully
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="admin@example.com", password="admin", name="adminuser")

    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignment to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "History 101"}),
        headers={"Content-Type": "application/json"},
    )

    class_id = class_response.json["class"]["id"]

    # Now, create the assignment
    future_date = datetime.datetime.now() + timedelta(days=30)
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {"courseID": class_id, "name": "Essay 1", "rubric": "Quality of writing", "due_date": future_date.isoformat()}
        ),
        headers={"Content-Type": "application/json"},
    )
    
    assert assignment_response.status_code == 201
    assert assignment_response.json["msg"] == "Assignment created"
    assert assignment_response.json["assignment"]["name"] == "Essay 1"
    assert assignment_response.json["assignment"]["rubric_text"] == "Quality of writing"
    # Check that due_date is approximately correct (same day)
    assert assignment_response.json["assignment"]["due_date"].startswith(future_date.strftime("%Y-%m-%d"))


def test_create_assignment_missing_fields(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to create an assignment with missing fields
    THEN the API should return a 400 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="admin@example.com", password="admin", name="adminuser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to create an assignment without a class_id
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"name": "Essay 1", "rubric": "Quality of writing"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Course ID is required"

    # Attempt to create an assignment without a name
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": 1, "rubric": "Quality of writing"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "Assignment name is required"


def test_teacher_can_create_assignment_with_description_start_and_due_dates(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they create an assignment with description, start_date, and due_date
    THEN those metadata fields should be persisted and returned
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US4 Metadata Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    start_date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).isoformat()
    due_date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat()

    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Milestone 1",
                "description": "Implement initial feature set",
                "start_date": start_date,
                "due_date": due_date,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 201
    assert response.json["assignment"]["name"] == "Milestone 1"
    assert response.json["assignment"]["description"] == "Implement initial feature set"
    assert response.json["assignment"]["start_date"].startswith(start_date[:10])
    assert response.json["assignment"]["due_date"].startswith(due_date[:10])


def test_create_assignment_defaults_to_anonymous(test_client, make_admin):
    """
    GIVEN a teacher creating an assignment without anonymity field
    WHEN assignment creation succeeds
    THEN the assignment defaults to anonymous submissions/reviews
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US9 Anonymous Default Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Anonymous by Default",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 201
    assert response.json["assignment"]["is_anonymous"] is True


def test_teacher_can_deanonymize_assignment_via_edit(test_client, make_admin):
    """
    GIVEN a teacher managing an assignment
    WHEN they set is_anonymous to false
    THEN the assignment becomes de-anonymized
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US9 De-anonymize Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    create_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Toggle Anonymity",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_response.json["assignment"]["id"]
    assert create_response.json["assignment"]["is_anonymous"] is True

    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"is_anonymous": False}),
        headers={"Content-Type": "application/json"},
    )

    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["is_anonymous"] is False

def test_non_assigned_teacher_cannot_create_assignment(test_client, make_admin):
    """
    GIVEN a teacher user who is not assigned to the class
    WHEN they try to create an assignment for that class
    THEN the API should return a 403 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    make_admin(email="otherteacher@example.com", password="otherteacher", name="otherteacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Create a class with a different teacher
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Log in as the other teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "otherteacher"}),
        headers={"Content-Type": "application/json"},
    )

    # Attempt to create an assignment for the class
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {"courseID": class_id, "name": "Homework 1", "rubric": "Accuracy"}
        ),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Unauthorized: You are not the teacher of this class"
def test_nonexistent_class_cannot_create_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to create an assignment for a non-existent class
    THEN the API should return a 404 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to create an assignment for a non-existent class
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {"courseID": 999, "name": "Homework 1", "rubric": "Accuracy"}
        ),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404
    assert response.json["msg"] == "Class not found"

def test_unauthenticated_user_cannot_create_assignment(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they try to create an assignment
    THEN the API should return a 401 error
    """
    # Attempt to create an assignment without logging in
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {"class_id": 1, "name": "Homework 1", "rubric": "Accuracy"}
        ),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401

# Test cases for editing and deleting assignments
def test_teacher_can_edit_assignment_before_due_date(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they edit an assignment before its due date
    THEN the assignment should be updated successfully
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignment to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, create the assignment with a future due date
    start_date = datetime.datetime.now(datetime.timezone.utc) + timedelta(days=1)
    future_date = datetime.datetime.now() + timedelta(days=60)
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Lab Report 1",
                "description": "Initial draft",
                "start_date": start_date.isoformat(),
                "rubric": "Completeness",
                "due_date": future_date.isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]
    # Now, edit the assignment
    new_due_date = datetime.datetime.now() + timedelta(days=30)
    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps(
            {
                "name": "Updated Lab Report 1",
                "description": "Revised report with final edits",
                "start_date": (datetime.datetime.now(datetime.timezone.utc) + timedelta(days=2)).isoformat(),
                "rubric": "Thoroughness",
                "due_date": new_due_date.isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json["msg"] == "Assignment updated"
    assert edit_response.json["assignment"]["name"] == "Updated Lab Report 1"
    assert edit_response.json["assignment"]["description"] == "Revised report with final edits"
    assert edit_response.json["assignment"]["rubric_text"] == "Thoroughness"
    # Check that due_date is approximately correct (same day)
    assert edit_response.json["assignment"]["due_date"].startswith(new_due_date.strftime("%Y-%m-%d"))

def test_teacher_can_edit_assignment_after_due_date(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to edit an assignment after its due date
    THEN the API should allow the edit and return 200
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignment to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Art 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, create the assignment with a past due date
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Painting 1",
                "rubric": "Creativity",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]
    # Now, attempt to edit the assignment
    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps(
            {
                "name": "Updated Painting 1",
                "rubric": "Originality",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["name"] == "Updated Painting 1"

def test_non_assigned_teacher_cannot_edit_assignment(test_client, make_admin):
    """
    GIVEN a teacher user who is not assigned to the class
    WHEN they try to edit an assignment for that class
    THEN the API should return a 403 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    make_admin(email="otherteacher@example.com", password="teacher", name="otherteacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignment to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Music 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, create the assignment
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Composition 1",
                "rubric": "Harmony",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=5)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]
    # Log in as the other teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Now, attempt to edit the assignment
    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps(
            {
                "name": "Updated Composition 1",
                "rubric": "Melody",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 403
    assert edit_response.json["msg"] == "Unauthorized: You are not the teacher of this class"

def test_unauthenticated_user_cannot_edit_assignment(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they try to edit an assignment
    THEN the API should return a 401 error
    """
    # Attempt to edit an assignment without logging in
    edit_response = test_client.patch(
        "/assignment/edit_assignment/1",
        data=json.dumps(
            {
                "name": "Updated Assignment",
                "rubric": "New Rubric",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 401


def test_student_cannot_edit_assignment(test_client, make_admin):
    """
    GIVEN a student user
    WHEN they try to edit an assignment
    THEN the API should return 403
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US4 Student Edit Restriction Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Read-only Assignment",
                "rubric": "Clarity",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "Student Editor",
                "email": "student.editor@example.com",
                "password": "studentpass",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student.editor@example.com", "password": "studentpass"}),
        headers={"Content-Type": "application/json"},
    )

    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"name": "Student Update Attempt"}),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 403
    assert edit_response.json["msg"] == "Insufficient permissions"

def test_edit_nonexistent_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to edit a non-existent assignment
    THEN the API should return a 404 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to edit a non-existent assignment
    edit_response = test_client.patch(
        "/assignment/edit_assignment/999",
        data=json.dumps(
            {
                "name": "Updated Assignment",
                "rubric": "New Rubric",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 404
    assert edit_response.json["msg"] == "Assignment not found"

def test_delete_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they delete an assignment before its due date
    THEN the assignment should be deleted successfully
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignment to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Philosophy 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, create the assignment with a future due date
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Essay on Ethics",
                "rubric": "Argumentation",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]
    # Now, delete the assignment
    delete_response = test_client.delete(
        f"/assignment/delete_assignment/{assignment_id}",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Assignment deleted"

def test_delete_assignment_after_due_date(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to delete an assignment after its due date
    THEN the API should allow the deletion and return 200
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignment to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Economics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, create the assignment with a past due date
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Market Analysis",
                "rubric": "Data Interpretation",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]
    # Now, attempt to delete the assignment
    delete_response = test_client.delete(
        f"/assignment/delete_assignment/{assignment_id}",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Assignment deleted"

def test_non_assigned_teacher_cannot_delete_assignment(test_client, make_admin):
    """
    GIVEN a teacher user who is not assigned to the class
    WHEN they try to delete an assignment for that class
    THEN the API should return a 403 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    make_admin(email="otherteacher@example.com", password="teacher", name="otherteacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignment to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Geography 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, create the assignment as the first teacher
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Geography Assignment",
                "rubric": "Map Skills",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    # Now, attempt to delete the assignment as the other teacher
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    delete_response = test_client.delete(
        f"/assignment/delete_assignment/{assignment_id}",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 403
    assert delete_response.json["msg"] == "Unauthorized: You are not the teacher of this class"

def test_unauthenticated_user_cannot_delete_assignment(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they try to delete an assignment
    THEN the API should return a 401 error
    """
    # Attempt to delete an assignment without logging in
    delete_response = test_client.delete(
        "/assignment/delete_assignment/1",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 401


def test_student_cannot_delete_assignment(test_client, make_admin):
    """
    GIVEN a student user
    WHEN they try to delete an assignment
    THEN the API should return 403
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US4 Student Delete Restriction Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Delete-protected Assignment",
                "rubric": "Depth",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "Student Deleter",
                "email": "student.deleter@example.com",
                "password": "studentpass",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student.deleter@example.com", "password": "studentpass"}),
        headers={"Content-Type": "application/json"},
    )

    delete_response = test_client.delete(
        f"/assignment/delete_assignment/{assignment_id}",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 403
    assert delete_response.json["msg"] == "Insufficient permissions"

def test_delete_nonexistent_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to delete a non-existent assignment
    THEN the API should return a 404 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to delete a non-existent assignment
    delete_response = test_client.delete(
        "/assignment/delete_assignment/999",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 404
    assert delete_response.json["msg"] == "Assignment not found"

def test_get_assignments_by_class_id(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they request assignments for a specific class
    THEN the API should return the list of assignments for that class
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class to assign the assignments to
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Literature 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, create multiple assignments for the class
    assignment_names = ["Poetry Analysis", "Novel Review", "Drama Essay"]
    for name in assignment_names:
        test_client.post(
            "/assignment/create_assignment",
            data=json.dumps(
                {
                    "courseID": class_id,
                    "name": name,
                    "rubric": "Content Quality",
                    "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)).isoformat(),
                }
            ),
            headers={"Content-Type": "application/json"},
        )
    # Now, retrieve assignments for the class
    assignments = test_client.get(f"/assignment/{class_id}")
    assert assignments.status_code == 200
    assert len(assignments.json) == 3
    returned_names = [assignment["name"] for assignment in assignments.json]
    for name in assignment_names:
        assert name in returned_names


def test_enrolled_student_can_see_assignments_for_class(test_client, make_admin):
    """
    GIVEN an enrolled student in a class
    WHEN the student requests assignments for that class
    THEN the API should return assignments successfully
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US4 Student Visibility Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Visible Assignment",
                "rubric": "Completion",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/class/enroll_students",
        data=json.dumps(
            {
                "class_id": class_id,
                "students": "id,name,email\n1,Student One,student.one@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student.one@example.com", "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )

    assignments_response = test_client.get(f"/assignment/{class_id}")
    assert assignments_response.status_code == 200
    assert len(assignments_response.json) == 1
    assert assignments_response.json[0]["name"] == "Visible Assignment"


def test_unenrolled_student_cannot_see_assignments_for_class(test_client, make_admin):
    """
    GIVEN a student not enrolled in a class
    WHEN the student requests assignments for that class
    THEN the API should return 403
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US4 Access Control Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Restricted Assignment",
                "rubric": "Completion",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "Unenrolled Student",
                "email": "student.two@example.com",
                "password": "studentpass",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "student.two@example.com", "password": "studentpass"}),
        headers={"Content-Type": "application/json"},
    )

    assignments_response = test_client.get(f"/assignment/{class_id}")
    assert assignments_response.status_code == 403
    assert assignments_response.json["msg"] == "Unauthorized: You do not have access to this class"

def test_get_assignments_by_class_id_no_assignments(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they request assignments for a class with no assignments
    THEN the API should return an empty list
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # First, create a class with no assignments
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Philosophy 102"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    # Now, retrieve assignments for the class
    assignments = test_client.get(f"/assignment/{class_id}")
    assert assignments.status_code == 200
    assert len(assignments.json) == 0

def test_get_assignments_by_class_id_nonexistent_class(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they request assignments for a non-existent class
    THEN the API should return a 404 error
    """
    # Use make_admin fixture to create a teacher user
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    # Create a teacher user and log in
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    # Attempt to retrieve assignments for a non-existent class
    assignments = test_client.get(f"/assignment/999")
    assert assignments.status_code == 404
    assert assignments.json["msg"] == "Class not found"


def test_get_assignments_by_class_id_includes_due_date_metadata(test_client, make_admin):
    """
    GIVEN a teacher with assignments in a class
    WHEN they request assignments for that class
    THEN each assignment payload includes key due date metadata
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US15 Metadata Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    due_date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).isoformat()
    test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Timed Assignment",
                "rubric": "Completeness",
                "due_date": due_date,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assignments_response = test_client.get(f"/assignment/{class_id}")
    assert assignments_response.status_code == 200
    assert len(assignments_response.json) == 1

    assignment_payload = assignments_response.json[0]
    assert "due_date" in assignment_payload
    assert assignment_payload["due_date"].startswith(due_date[:10])


def test_get_assignments_by_class_id_supports_missing_due_date_metadata(test_client, make_admin):
    """
    GIVEN a teacher with assignments without due dates
    WHEN they request assignments for that class
    THEN due date metadata is still present as null for frontend status handling
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US15 No Due Date Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Open Assignment",
                "rubric": "Participation",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assignments_response = test_client.get(f"/assignment/{class_id}")
    assert assignments_response.status_code == 200
    assert len(assignments_response.json) == 1

    assignment_payload = assignments_response.json[0]
    assert "due_date" in assignment_payload
    assert assignment_payload["due_date"] is None

def test_unauthenticated_user_cannot_get_assignments(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they try to get assignments for a class
    THEN the API should return a 401 error
    """
    # Attempt to retrieve assignments for a class without logging in
    assignments = test_client.get(f"/assignment/1")
    assert assignments.status_code == 401


def test_get_single_assignment(test_client, make_admin):
    """
    GIVEN an authenticated user
    WHEN they request a single assignment by ID
    THEN the assignment details should be returned with courseID
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    
    # Create a class
    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Test Course"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]
    
    # Create an assignment
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Test Assignment", "rubric": "Test rubric"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]
    
    # Get the single assignment
    response = test_client.get(f"/assignment/detail/{assignment_id}")
    
    assert response.status_code == 200
    assert response.json["id"] == assignment_id
    assert response.json["name"] == "Test Assignment"
    assert response.json["courseID"] == class_id  # Verify courseID is included


def test_enrolled_student_can_get_single_assignment_detail(test_client, make_admin):
    """
    GIVEN an enrolled student
    WHEN they request assignment detail
    THEN the API should return assignment details
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US4 Detail Access Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Detail Visible Assignment", "rubric": "Clarity"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    test_client.post(
        "/class/enroll_students",
        data=json.dumps(
            {
                "class_id": class_id,
                "students": "id,name,email\n1,Detail Student,detail.student@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "detail.student@example.com", "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get(f"/assignment/detail/{assignment_id}")
    assert response.status_code == 200
    assert response.json["id"] == assignment_id
    assert response.json["courseID"] == class_id


def test_unenrolled_student_cannot_get_single_assignment_detail(test_client, make_admin):
    """
    GIVEN a student not enrolled in a class
    WHEN they request assignment detail for that class
    THEN the API should return 403
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "US4 Detail Restricted Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Detail Restricted Assignment", "rubric": "Coverage"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "Unenrolled Detail Student",
                "email": "detail.unenrolled@example.com",
                "password": "studentpass",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "detail.unenrolled@example.com", "password": "studentpass"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.get(f"/assignment/detail/{assignment_id}")
    assert response.status_code == 403
    assert response.json["msg"] == "Unauthorized: You do not have access to this class"


def test_get_nonexistent_assignment(test_client, make_admin):
    """
    GIVEN an authenticated user
    WHEN they request an assignment that doesn't exist
    THEN a 404 error should be returned
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    
    response = test_client.get("/assignment/detail/9999")

    assert response.status_code == 404
    assert response.json["msg"] == "Assignment not found"


# ============================================================================
# REVIEW SETTINGS (individual_reviews / group_reviews)
# ============================================================================


def test_create_assignment_defaults_review_types_enabled(test_client, make_admin):
    """New assignments default to both individual_reviews and group_reviews enabled."""
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    class_resp = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Review Settings Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_resp.json["class"]["id"]

    resp = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "HW1"}),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 201
    assignment = resp.json["assignment"]
    assert assignment["individual_reviews"] is True
    assert assignment["group_reviews"] is True


def test_create_assignment_with_review_types_disabled(test_client, make_admin):
    """Teacher can create an assignment with review types explicitly disabled."""
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    class_resp = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Review Settings Class 2"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_resp.json["class"]["id"]

    resp = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({
            "courseID": class_id,
            "name": "HW2",
            "individual_reviews": False,
            "group_reviews": False,
        }),
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 201
    assignment = resp.json["assignment"]
    assert assignment["individual_reviews"] is False
    assert assignment["group_reviews"] is False


def test_edit_assignment_review_types(test_client, make_admin):
    """Teacher can toggle review types via edit."""
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )
    class_resp = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Review Settings Edit Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_resp.json["class"]["id"]

    create_resp = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "HW3"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = create_resp.json["assignment"]["id"]

    # Disable group reviews
    edit_resp = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"group_reviews": False}),
        headers={"Content-Type": "application/json"},
    )
    assert edit_resp.status_code == 200
    assert edit_resp.json["assignment"]["group_reviews"] is False
    assert edit_resp.json["assignment"]["individual_reviews"] is True

    # Disable individual, re-enable group
    edit_resp2 = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"individual_reviews": False, "group_reviews": True}),
        headers={"Content-Type": "application/json"},
    )
    assert edit_resp2.status_code == 200
    assert edit_resp2.json["assignment"]["individual_reviews"] is False
    assert edit_resp2.json["assignment"]["group_reviews"] is True