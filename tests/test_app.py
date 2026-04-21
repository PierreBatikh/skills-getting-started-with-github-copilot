"""Comprehensive tests for the Mergington High School Activities API using AAA pattern."""
import pytest


class TestRootEndpoint:
    """Tests for GET / endpoint."""

    def test_root_redirects_to_static_index(self, client):
        """Root endpoint should redirect to /static/index.html."""
        # Arrange
        expected_redirect_path = "/static/index.html"

        # Act
        response = client.get("/", follow_redirects=False)

        # Assert
        assert response.status_code == 307
        assert expected_redirect_path in response.headers.get("location", "")


class TestGetActivities:
    """Tests for GET /activities endpoint."""

    def test_get_all_activities(self, client):
        """Should return all activities with correct structure."""
        # Arrange
        expected_activity_count = 9
        activity_name = "Chess Club"

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert
        assert response.status_code == 200
        assert isinstance(data, dict)
        assert len(data) == expected_activity_count
        assert activity_name in data
        assert "description" in data[activity_name]
        assert "schedule" in data[activity_name]
        assert "max_participants" in data[activity_name]
        assert "participants" in data[activity_name]

    def test_activity_structure_contains_required_fields(self, client):
        """Each activity should have all required fields."""
        # Arrange
        required_fields = ["description", "schedule", "max_participants", "participants"]

        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity in activities_data.items():
            for field in required_fields:
                assert field in activity, f"Missing field '{field}' in {activity_name}"
            assert isinstance(activity["participants"], list)
            assert isinstance(activity["max_participants"], int)
            assert activity["max_participants"] > 0

    def test_chess_club_has_initial_participants(self, client):
        """Chess Club should have its initial participants."""
        # Arrange
        expected_participants = ["michael@mergington.edu", "daniel@mergington.edu"]

        # Act
        response = client.get("/activities")
        chess_club = response.json()["Chess Club"]

        # Assert
        assert chess_club["participants"] == expected_participants


class TestSignUp:
    """Tests for POST /activities/{activity_name}/signup endpoint."""

    def test_signup_new_participant_success(self, client):
        """Successfully sign up a new participant for an activity."""
        # Arrange
        activity_name = "Chess Club"
        new_email = "newstudent@mergington.edu"
        initial_count = 2

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        updated_activities = client.get("/activities").json()
        updated_participants = updated_activities[activity_name]["participants"]

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
        assert new_email in updated_participants
        assert len(updated_participants) == initial_count + 1

    def test_signup_duplicate_participant_fails(self, client):
        """Attempting to sign up an existing participant should fail."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"
        expected_status = 400
        expected_detail = "already signed up"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        response_data = response.json()

        # Assert
        assert response.status_code == expected_status
        assert expected_detail in response_data["detail"]

    def test_signup_nonexistent_activity_fails(self, client):
        """Signing up for a non-existent activity should fail."""
        # Arrange
        nonexistent_activity = "Nonexistent Club"
        email = "student@mergington.edu"
        expected_status = 404

        # Act
        response = client.post(
            f"/activities/{nonexistent_activity}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == expected_status
        assert "Activity not found" in response.json()["detail"]

    def test_signup_with_url_encoded_activity_name(self, client):
        """Signup should handle URL-encoded activity names."""
        # Arrange
        activity_name_encoded = "Programming%20Class"
        activity_name_decoded = "Programming Class"
        new_email = "test@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name_encoded}/signup",
            params={"email": new_email}
        )
        activities_data = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert new_email in activities_data[activity_name_decoded]["participants"]

    def test_signup_with_special_characters_in_email(self, client):
        """Email with special characters should be accepted."""
        # Arrange
        activity_name = "Chess Club"
        special_email = "student+test@sub.mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": special_email}
        )
        activities_data = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert special_email in activities_data[activity_name]["participants"]

    def test_signup_multiple_students_same_activity(self, client):
        """Multiple different students can sign up for the same activity."""
        # Arrange
        activity_name = "Art Studio"
        initial_count = len(client.get("/activities").json()[activity_name]["participants"])
        new_emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]

        # Act
        for email in new_emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        updated_activities = client.get("/activities").json()
        updated_participants = updated_activities[activity_name]["participants"]

        # Assert
        for email in new_emails:
            assert email in updated_participants
        assert len(updated_participants) == initial_count + len(new_emails)

    def test_signup_missing_email_parameter_fails(self, client):
        """Signup without email parameter should fail with validation error."""
        # Arrange
        activity_name = "Chess Club"
        expected_status = 422  # Unprocessable Entity

        # Act
        response = client.post(f"/activities/{activity_name}/signup")

        # Assert
        assert response.status_code == expected_status

    def test_signup_case_sensitive_activity_name(self, client):
        """Activity names should be case-sensitive."""
        # Arrange
        correct_name = "Chess Club"
        wrong_case_name = "chess club"
        email = "test@mergington.edu"
        expected_status = 404

        # Act
        response = client.post(
            f"/activities/{wrong_case_name}/signup",
            params={"email": email}
        )

        # Assert
        assert response.status_code == expected_status
        assert "Activity not found" in response.json()["detail"]


class TestUnregister:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint."""

    def test_unregister_existing_participant_success(self, client):
        """Successfully unregister an existing participant."""
        # Arrange
        activity_name = "Chess Club"
        email_to_remove = "michael@mergington.edu"
        initial_response = client.get("/activities").json()
        initial_count = len(initial_response[activity_name]["participants"])

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_to_remove}
        )
        updated_activities = client.get("/activities").json()
        updated_participants = updated_activities[activity_name]["participants"]

        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email_to_remove} from {activity_name}"
        assert email_to_remove not in updated_participants
        assert len(updated_participants) == initial_count - 1

    def test_unregister_nonexistent_participant_fails(self, client):
        """Attempting to unregister a non-signed-up participant should fail."""
        # Arrange
        activity_name = "Chess Club"
        email_not_signed_up = "nobody@mergington.edu"
        expected_status = 400

        # Act
        response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email_not_signed_up}
        )

        # Assert
        assert response.status_code == expected_status
        assert "not signed up" in response.json()["detail"]

    def test_unregister_from_nonexistent_activity_fails(self, client):
        """Unregistering from a non-existent activity should fail."""
        # Arrange
        fake_activity = "Fake Activity"
        email = "student@mergington.edu"
        expected_status = 404

        # Act
        response = client.delete(
            f"/activities/{fake_activity}/unregister",
            params={"email": email}
        )

        # Assert
        assert response.status_code == expected_status
        assert "Activity not found" in response.json()["detail"]

    def test_unregister_with_url_encoded_activity_name(self, client):
        """Unregister should handle URL-encoded activity names."""
        # Arrange
        activity_name_encoded = "Programming%20Class"
        activity_name_decoded = "Programming Class"
        email = "emma@mergington.edu"  # Already signed up

        # Act
        response = client.delete(
            f"/activities/{activity_name_encoded}/unregister",
            params={"email": email}
        )
        updated_activities = client.get("/activities").json()

        # Assert
        assert response.status_code == 200
        assert email not in updated_activities[activity_name_decoded]["participants"]

    def test_unregister_missing_email_parameter_fails(self, client):
        """Unregister without email parameter should fail."""
        # Arrange
        activity_name = "Chess Club"
        expected_status = 422

        # Act
        response = client.delete(f"/activities/{activity_name}/unregister")

        # Assert
        assert response.status_code == expected_status

    def test_signup_after_unregister(self, client):
        """A participant should be able to sign up again after unregistering."""
        # Arrange
        activity_name = "Chess Club"
        email = "michael@mergington.edu"

        # Act - Unregister
        unregister_response = client.delete(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Act - Sign up again
        signup_response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Check final state
        final_activities = client.get("/activities").json()

        # Assert
        assert unregister_response.status_code == 200
        assert signup_response.status_code == 200
        assert email in final_activities[activity_name]["participants"]


class TestDataIntegrity:
    """Tests for data integrity and state management."""

    def test_signup_does_not_affect_other_activities(self, client):
        """Signup for one activity shouldn't affect other activities."""
        # Arrange
        test_activity = "Chess Club"
        unrelated_activity = "Gym Class"
        new_email = "newstudent@mergington.edu"
        original_gym_participants = client.get("/activities").json()[unrelated_activity]["participants"].copy()

        # Act
        client.post(
            f"/activities/{test_activity}/signup",
            params={"email": new_email}
        )
        
        final_gym_participants = client.get("/activities").json()[unrelated_activity]["participants"]

        # Assert
        assert final_gym_participants == original_gym_participants

    def test_unregister_does_not_affect_other_activities(self, client):
        """Unregister from one activity shouldn't affect other activities."""
        # Arrange
        test_activity = "Chess Club"
        unrelated_activity = "Gym Class"
        email_to_remove = "michael@mergington.edu"
        original_gym_participants = client.get("/activities").json()[unrelated_activity]["participants"].copy()

        # Act
        client.delete(
            f"/activities/{test_activity}/unregister",
            params={"email": email_to_remove}
        )
        
        final_gym_participants = client.get("/activities").json()[unrelated_activity]["participants"]

        # Assert
        assert final_gym_participants == original_gym_participants

    def test_participant_count_matches_list_length(self, client):
        """Participant list length should always match expected count."""
        # Arrange
        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity in activities_data.items():
            actual_list_length = len(activity["participants"])
            assert isinstance(actual_list_length, int)
            assert activity["max_participants"] > 0
            assert actual_list_length <= activity["max_participants"]

    def test_no_duplicate_participants_in_activity(self, client):
        """No duplicate participants should exist in any activity."""
        # Arrange
        # Act
        response = client.get("/activities")
        activities_data = response.json()

        # Assert
        for activity_name, activity in activities_data.items():
            participants = activity["participants"]
            unique_participants = set(participants)
            assert len(participants) == len(unique_participants), \
                f"Duplicates found in {activity_name}: {participants}"


class TestResponseValidation:
    """Tests for response validation and format."""

    def test_success_response_structure(self, client):
        """Success responses should have consistent structure."""
        # Arrange
        activity_name = "Chess Club"
        email = "newstudent@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        response_body = response.json()

        # Assert
        assert "message" in response_body
        assert isinstance(response_body["message"], str)
        assert len(response_body["message"]) > 0

    def test_error_response_has_detail_field(self, client):
        """Error responses should include detail field."""
        # Arrange
        activity_name = "Chess Club"
        existing_email = "michael@mergington.edu"

        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        response_body = response.json()

        # Assert
        assert "detail" in response_body
        assert isinstance(response_body["detail"], str)

    def test_activities_response_is_valid_json(self, client):
        """Activities response should be valid JSON."""
        # Arrange
        import json

        # Act
        response = client.get("/activities")
        data = response.json()

        # Assert - Should not raise exception
        serialized = json.dumps(data)
        assert len(serialized) > 0
        deserialized = json.loads(serialized)
        assert deserialized == data
