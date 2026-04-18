import json


def test_change_password(test_client):
    """
    GIVEN PUT /auth/change-password
    WHEN a logged-in user provides correct current password and a new password
    THEN the password should be updated successfully
    """
    # Step 1: Register a user
    test_client.post(
        "/auth/register",
        data=json.dumps({"name": "testuser", "password": "oldpassword", "email": "testuser@example.com"}),
        headers={"Content-Type": "application/json"},
    )

    # Step 2: Login (cookie is stored automatically)
    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "testuser@example.com", "password": "oldpassword"}),
        headers={"Content-Type": "application/json"},
    )

    # Step 3: Change password
    response = test_client.put(
        "/auth/change-password",
        data=json.dumps({"current_password": "oldpassword", "new_password": "newpassword"}),
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json["msg"] == "Password updated successfully"