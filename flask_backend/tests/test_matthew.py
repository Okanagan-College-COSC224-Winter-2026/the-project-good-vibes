"""
Tests for practice endpoint
"""


def test_practice_endpoint(test_client):
    """
    GIVEN a Flask application
    WHEN GET /practice/test is called
    THEN it should return course information with status 200
    """
    # Send GET request to the endpoint
    response = test_client.get("/practice/test")
    
    # Assert status code is 200
    assert response.status_code == 200
    
    # Assert response is not null
    assert response.data is not None
    
    # Get JSON data from response
    data = response.get_json()
    
    # Assert 'course' key is present and has correct value
    assert 'course' in data
    assert data['course'] == 'cosc 224'
