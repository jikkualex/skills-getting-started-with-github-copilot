"""Tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app, activities

# Create a test client
client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        k: {**v, "participants": v["participants"].copy()}
        for k, v in activities.items()
    }
    
    yield
    
    # Restore original state after test
    for activity_name, activity_data in original_activities.items():
        activities[activity_name]["participants"] = activity_data["participants"].copy()


class TestGetActivities:
    """Test the GET /activities endpoint"""
    
    def test_get_activities_returns_dict(self):
        """Test that /activities returns a dictionary of activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
    
    def test_get_activities_contains_expected_activities(self):
        """Test that /activities contains all expected activities"""
        response = client.get("/activities")
        data = response.json()
        
        expected_activities = [
            "Basketball", "Soccer", "Art Club", "Drama Club",
            "Robotics Club", "Debate Team", "Chess Club",
            "Programming Class", "Gym Class"
        ]
        
        for activity in expected_activities:
            assert activity in data
    
    def test_activity_structure(self):
        """Test that each activity has the expected structure"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)


class TestSignupForActivity:
    """Test the POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_successful(self, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "test@mergington.edu" in activities["Basketball"]["participants"]
    
    def test_signup_activity_not_found(self, reset_activities):
        """Test signup to non-existent activity"""
        response = client.post(
            "/activities/NonExistent/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, reset_activities):
        """Test signup with email already registered for activity"""
        # Alex is already in Basketball
        response = client.post(
            "/activities/Basketball/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_adds_to_participants_list(self, reset_activities):
        """Test that signup adds participant to list"""
        initial_count = len(activities["Soccer"]["participants"])
        
        response = client.post(
            "/activities/Soccer/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        assert len(activities["Soccer"]["participants"]) == initial_count + 1
        assert "newstudent@mergington.edu" in activities["Soccer"]["participants"]


class TestUnregisterFromActivity:
    """Test the POST /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_successful(self, reset_activities):
        """Test successful unregister from an activity"""
        # Add a participant first
        activities["Basketball"]["participants"].append("temp@mergington.edu")
        
        response = client.post(
            "/activities/Basketball/unregister?email=temp@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "temp@mergington.edu" not in activities["Basketball"]["participants"]
    
    def test_unregister_activity_not_found(self, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.post(
            "/activities/NonExistent/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Activity not found"
    
    def test_unregister_email_not_registered(self, reset_activities):
        """Test unregister with email not registered for activity"""
        response = client.post(
            "/activities/Basketball/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not signed up" in data["detail"]
    
    def test_unregister_removes_from_participants_list(self, reset_activities):
        """Test that unregister removes participant from list"""
        # Verify initial state
        assert "alex@mergington.edu" in activities["Basketball"]["participants"]
        initial_count = len(activities["Basketball"]["participants"])
        
        response = client.post(
            "/activities/Basketball/unregister?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        
        assert len(activities["Basketball"]["participants"]) == initial_count - 1
        assert "alex@mergington.edu" not in activities["Basketball"]["participants"]


class TestRootEndpoint:
    """Test the root endpoint"""
    
    def test_root_redirects_to_static(self):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code in [301, 302, 307, 308]
        assert "/static/index.html" in response.headers["location"]
