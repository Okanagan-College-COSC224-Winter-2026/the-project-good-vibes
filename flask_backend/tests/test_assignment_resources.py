import io
import json


def _setup_class_and_assignment(test_client):
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Resource Class"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Resource Assignment"}),
        headers={"Content-Type": "application/json"},
    )

    return class_id, assignment_response.json["assignment"]["id"]


def test_teacher_can_upload_and_delete_assignment_resource(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    _, assignment_id = _setup_class_and_assignment(test_client)

    upload_response = test_client.post(
        f"/assignment-resource/assignment/{assignment_id}",
        data={"file": (io.BytesIO(b"course document"), "supporting.pdf")},
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 201
    resource_id = upload_response.json["resource"]["id"]
    assert upload_response.json["resource"]["original_name"] == "supporting.pdf"

    list_response = test_client.get(f"/assignment-resource/assignment/{assignment_id}")
    assert list_response.status_code == 200
    assert len(list_response.json["resources"]) == 1

    delete_response = test_client.delete(f"/assignment-resource/{resource_id}")
    assert delete_response.status_code == 200


def test_enrolled_student_can_view_assignment_resources(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    class_id, assignment_id = _setup_class_and_assignment(test_client)

    test_client.post(
        f"/assignment-resource/assignment/{assignment_id}",
        data={"file": (io.BytesIO(b"guide"), "guide.txt")},
        content_type="multipart/form-data",
    )

    test_client.post(
        "/class/enroll_students",
        data=json.dumps(
            {
                "class_id": class_id,
                "students": "id,name,email\n1,Resource Student,resource.student@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "resource.student@example.com", "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )

    list_response = test_client.get(f"/assignment-resource/assignment/{assignment_id}")
    assert list_response.status_code == 200
    assert len(list_response.json["resources"]) == 1
    assert list_response.json["resources"][0]["original_name"] == "guide.txt"


def test_student_cannot_upload_assignment_resources(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    class_id, assignment_id = _setup_class_and_assignment(test_client)

    test_client.post(
        "/class/enroll_students",
        data=json.dumps(
            {
                "class_id": class_id,
                "students": "id,name,email\n1,Blocked Student,blocked.student@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "blocked.student@example.com", "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )

    upload_response = test_client.post(
        f"/assignment-resource/assignment/{assignment_id}",
        data={"file": (io.BytesIO(b"nope"), "student.pdf")},
        content_type="multipart/form-data",
    )

    assert upload_response.status_code == 403
    assert upload_response.json["msg"] == "Insufficient permissions"


def test_enrolled_student_can_download_assignment_resource(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    class_id, assignment_id = _setup_class_and_assignment(test_client)

    upload_response = test_client.post(
        f"/assignment-resource/assignment/{assignment_id}",
        data={"file": (io.BytesIO(b"resource bytes"), "resource.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 201
    resource_id = upload_response.json["resource"]["id"]

    test_client.post(
        "/class/enroll_students",
        data=json.dumps(
            {
                "class_id": class_id,
                "students": "id,name,email\n1,Download Student,download.student@example.com",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "download.student@example.com", "password": "password123"}),
        headers={"Content-Type": "application/json"},
    )

    download_response = test_client.get(f"/assignment-resource/file/{resource_id}")
    assert download_response.status_code == 200
    assert download_response.data == b"resource bytes"


def test_student_outside_course_cannot_download_assignment_resource(test_client, make_admin):
    make_admin(email="teacher@example.com", password="teacher", name="Teacher")
    _, assignment_id = _setup_class_and_assignment(test_client)

    upload_response = test_client.post(
        f"/assignment-resource/assignment/{assignment_id}",
        data={"file": (io.BytesIO(b"secret bytes"), "secret.txt")},
        content_type="multipart/form-data",
    )
    assert upload_response.status_code == 201
    resource_id = upload_response.json["resource"]["id"]

    test_client.post(
        "/auth/register",
        data=json.dumps(
            {
                "name": "Outside Student",
                "email": "outside.student@example.com",
                "password": "outsidepass",
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "outside.student@example.com", "password": "outsidepass"}),
        headers={"Content-Type": "application/json"},
    )

    download_response = test_client.get(f"/assignment-resource/file/{resource_id}")
    assert download_response.status_code == 403
    assert download_response.json["msg"] == "Unauthorized: You do not have access to this class"
