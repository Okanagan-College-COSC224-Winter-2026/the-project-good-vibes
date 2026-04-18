import datetime
import io
import json


def _setup_course_assignment_and_student(test_client):
    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "Submission Student",
                "email": "submission.student@example.com",
                "password": "studentpass",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Submission Test Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    test_client.post(
        "/class/enroll_students",
        data=json.dumps(
            {
                "class_id": class_id,
                "students": "id,name,email\n1,Submission Student,submission.student@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    due_date = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).isoformat()
    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Submission Assignment",
                "due_date": due_date,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assignment_id = assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "submission.student@example.com", "password": "studentpass"}),
        headers={"Content-Type": "application/json"},
    )

    return assignment_id


def test_student_can_upload_replace_and_remove_attachment(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")
    assignment_id = _setup_course_assignment_and_student(test_client)

    upload_response = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"hello world"), "draft.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    assert upload_response.json["submission"]["filename"].endswith("draft.txt")

    replace_response = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"updated contents"), "final.txt")},
        content_type="multipart/form-data",
    )
    assert replace_response.status_code == 200
    assert replace_response.json["submission"]["filename"].endswith("final.txt")

    get_response = test_client.get(f"/submission/{assignment_id}/mine")
    assert get_response.status_code == 200
    assert get_response.json["submission"]["filename"].endswith("final.txt")

    delete_response = test_client.delete(f"/submission/{assignment_id}/mine")
    assert delete_response.status_code == 200

    get_after_delete_response = test_client.get(f"/submission/{assignment_id}/mine")
    assert get_after_delete_response.status_code == 200
    assert get_after_delete_response.json["submission"] is None


def test_student_upload_requires_file(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")
    assignment_id = _setup_course_assignment_and_student(test_client)

    response = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert response.json["msg"] == "No file provided"


def test_teacher_cannot_upload_student_attachment(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Teacher Restriction Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Teacher Cannot Upload"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    response = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"teacher attempt"), "teacher.txt")},
        content_type="multipart/form-data",
    )

    assert response.status_code == 403
    assert response.json["msg"] == "Insufficient permissions"


def test_student_can_download_own_attachment(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")
    assignment_id = _setup_course_assignment_and_student(test_client)

    upload_response = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"download me"), "mine.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200

    submission_id = upload_response.json["submission"]["id"]
    download_response = test_client.get(f"/submission/file/{submission_id}")

    assert download_response.status_code == 200
    assert download_response.data == b"download me"


def test_student_cannot_download_other_students_attachment(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher User")
    assignment_id = _setup_course_assignment_and_student(test_client)

    upload_response = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"private file"), "private.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 200
    submission_id = upload_response.json["submission"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "Other Student",
                "email": "other.student@example.com",
                "password": "studentpass",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "other.student@example.com", "password": "studentpass"}),
        headers={"Content-Type": "application/json"},
    )

    download_response = test_client.get(f"/submission/file/{submission_id}")
    assert download_response.status_code == 403


# ---------------------------------------------------------------------------
# Group submission visibility
# ---------------------------------------------------------------------------


def _setup_group_with_two_students(test_client):
    """Create a course, assignment, group, and two enrolled students in the same group.

    The enroll endpoint auto-creates students with default password "password123".
    Returns (assignment_id, student_a_email, student_b_email).
    """
    student_a = "group.alice@example.com"
    student_b = "group.bob@example.com"

    # Teacher creates course, enrolls both, creates assignment and group
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_resp = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Group Submission Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_resp.json["class"]["id"]

    test_client.post(
        "/class/enroll_students",
        data=json.dumps({
            "class_id": class_id,
            "students": f"id,name,email\n1,Alice,{student_a}\n2,Bob,{student_b}",
        }),
        headers={"Content-Type": "application/json"},
    )

    due = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3)).isoformat()
    assign_resp = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Group Assignment", "due_date": due}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assign_resp.json["assignment"]["id"]

    group_resp = test_client.post(
        "/groups/create",
        data=json.dumps({"courseID": class_id, "name": "Team One"}),
        headers={"Content-Type": "application/json"},
    )
    group_id = group_resp.json["id"]

    # Get enrolled student IDs via class members endpoint
    members_resp = test_client.post(
        "/class/members",
        data=json.dumps({"id": class_id}),
        headers={"Content-Type": "application/json"},
    )
    members = members_resp.json
    alice_id = next(m["id"] for m in members if m["email"] == student_a)
    bob_id = next(m["id"] for m in members if m["email"] == student_b)

    test_client.post(
        "/groups/members/add",
        data=json.dumps({"groupID": group_id, "userID": alice_id}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/groups/members/add",
        data=json.dumps({"groupID": group_id, "userID": bob_id}),
        headers={"Content-Type": "application/json"},
    )

    return assignment_id, student_a, student_b


def test_group_member_can_see_group_submission(test_client, make_admin):
    """A group member can see a submission uploaded by another group member."""
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    assignment_id, alice_email, bob_email = _setup_group_with_two_students(test_client)

    # Alice uploads
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": alice_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    upload_resp = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"alice's work"), "report.txt")},
        content_type="multipart/form-data",
    )
    assert upload_resp.status_code == 200

    # Bob can see it
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": bob_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    get_resp = test_client.get(f"/submission/{assignment_id}/mine")
    assert get_resp.status_code == 200
    assert get_resp.json["submission"] is not None
    assert get_resp.json["submission"]["filename"].endswith("report.txt")


def test_group_member_can_download_group_submission(test_client, make_admin):
    """A group member can download a file uploaded by another group member."""
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    assignment_id, alice_email, bob_email = _setup_group_with_two_students(test_client)

    # Alice uploads
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": alice_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    upload_resp = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"downloadable"), "file.txt")},
        content_type="multipart/form-data",
    )
    submission_id = upload_resp.json["submission"]["id"]

    # Bob downloads it
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": bob_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    dl_resp = test_client.get(f"/submission/file/{submission_id}")
    assert dl_resp.status_code == 200
    assert dl_resp.data == b"downloadable"


def test_group_member_can_replace_group_submission(test_client, make_admin):
    """A group member can replace a submission uploaded by another group member."""
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    assignment_id, alice_email, bob_email = _setup_group_with_two_students(test_client)

    # Alice uploads
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": alice_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"v1"), "draft.txt")},
        content_type="multipart/form-data",
    )

    # Bob replaces it
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": bob_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    replace_resp = test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"v2"), "final.txt")},
        content_type="multipart/form-data",
    )
    assert replace_resp.status_code == 200
    assert replace_resp.json["submission"]["filename"].endswith("final.txt")

    # Alice sees the replaced version
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": alice_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    get_resp = test_client.get(f"/submission/{assignment_id}/mine")
    assert get_resp.json["submission"]["filename"].endswith("final.txt")


def test_group_member_can_delete_group_submission(test_client, make_admin):
    """A group member can delete a submission uploaded by another group member."""
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    assignment_id, alice_email, bob_email = _setup_group_with_two_students(test_client)

    # Alice uploads
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": alice_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        f"/submission/{assignment_id}/mine",
        data={"file": (io.BytesIO(b"to be deleted"), "temp.txt")},
        content_type="multipart/form-data",
    )

    # Bob deletes it
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": bob_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    del_resp = test_client.delete(f"/submission/{assignment_id}/mine")
    assert del_resp.status_code == 200

    # Alice sees no submission
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": alice_email, "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )
    get_resp = test_client.get(f"/submission/{assignment_id}/mine")
    assert get_resp.json["submission"] is None
