import json
import os

CURRENT_DIRECTORY = os.path.dirname(os.path.abspath(__file__))


def test_practice(test_client):
    """
    GIVEN GET /practice/test
    WHEN a test
    THEN a result
    """
    response = test_client.get(
        "/practice/test",
        data=json.dumps({"name": "testuser", "password": "123456", "email": "test@example.com"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 200
    assert response.json is not None
    assert response.json['course'] == 'cosc 224'
    assert 1 == 1



#  1. Open your project in the IDE of your choice (VS Code is recommended).
#  2. Go to the test directory and create a new file named test_your_name.py. This file can be a copy of any other test file.
#  3. Implement a unit test to test an HTTP GET request to http://localhost/practice/test.
#  4. In your API (HTTP endpoint), return a JSON object with course as the key and cosc 224 as the value.
#  5. In your unit test, assert that the status code is 200, the response is not null, and the value for course is present.
#  6. Run your test and make sure that it passes.