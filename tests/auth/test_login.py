import json
import pytest
from flask import url_for


class TestLogin:
    """Tests for the login endpoint."""

    def test_successful_login_with_email(self, client, test_user):
        """Test successful login with email as identifier."""
        response = client.post(
            url_for("auth.login"),
            json={
                "username": "user@test.com",  # Using email as the login identifier
                "password": "Password123!",
            },
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify response structure - tokens are returned
        assert "access_token" in data
        assert "refresh_token" in data

        # Verify token types
        assert len(data["access_token"]) > 20
        assert len(data["refresh_token"]) > 20

    def test_successful_login_with_username(self, client, test_user):
        """Test successful login with username as identifier."""
        response = client.post(
            url_for("auth.login"),
            json={
                "username": "testuser",  # Using actual username
                "password": "Password123!",
            },
        )

        assert response.status_code == 200
        data = response.get_json()

        # Verify successful authentication
        assert "access_token" in data
        assert "refresh_token" in data

    def test_login_invalid_credentials(self, client, test_user):
        """Test login attempt with non-existent email/username."""
        response = client.post(
            url_for("auth.login"),
            json={"username": "nonexistent@test.com", "password": "Password123!"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_login_wrong_password(self, client, test_user):
        """Test login attempt with incorrect password."""
        response = client.post(
            url_for("auth.login"),
            json={"username": "user@test.com", "password": "WrongPassword123!"},
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_login_missing_fields(self, client):
        """Test login attempt with missing required fields."""
        # Missing username
        response1 = client.post(
            url_for("auth.login"), json={"password": "Password123!"}
        )
        assert response1.status_code == 400
        assert "error" in response1.json

        # Missing password
        response2 = client.post(
            url_for("auth.login"), json={"username": "user@test.com"}
        )
        assert response2.status_code == 400
        assert "error" in response2.json
