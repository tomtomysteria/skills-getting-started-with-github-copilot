"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to a known state before each test"""
    # Store original participants
    original_participants = {
        name: list(data["participants"]) for name, data in activities.items()
    }
    yield
    # Restore original participants after each test
    for name, participants in original_participants.items():
        activities[name]["participants"] = participants


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self, client):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self, client):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)

    def test_get_activities_contains_expected_keys(self, client):
        """Test that activities contain expected structure"""
        response = client.get("/activities")
        data = response.json()
        
        assert len(data) > 0
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data


class TestSignup:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_registration(self, client):
        """Test that duplicate signup returns 400"""
        # First signup
        client.post("/activities/Basketball Team/signup?email=test@mergington.edu")
        # Duplicate signup
        response = client.post(
            "/activities/Basketball Team/signup?email=test@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_adds_participant(self, client):
        """Test that signup actually adds participant to the list"""
        email = "participant@mergington.edu"
        client.post(f"/activities/Tennis Club/signup?email={email}")
        
        response = client.get("/activities")
        assert email in response.json()["Tennis Club"]["participants"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # First register
        email = "tounregister@mergington.edu"
        client.post(f"/activities/Art Studio/signup?email={email}")
        
        # Then unregister
        response = client.delete(
            f"/activities/Art Studio/unregister?email={email}"
        )
        assert response.status_code == 200
        assert "Unregistered" in response.json()["message"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_not_registered(self, client):
        """Test unregister when not registered returns 400"""
        response = client.delete(
            "/activities/Debate Team/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from the list"""
        # Use an existing participant
        email = "noah@mergington.edu"
        
        # Verify they are registered
        response = client.get("/activities")
        assert email in response.json()["Debate Team"]["participants"]
        
        # Unregister
        client.delete(f"/activities/Debate Team/unregister?email={email}")
        
        # Verify they are no longer registered
        response = client.get("/activities")
        assert email not in response.json()["Debate Team"]["participants"]


class TestRootRedirect:
    """Tests for GET / endpoint"""

    def test_root_redirects(self, client):
        """Test that root path redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]
