import json
import pytest
from unittest.mock import patch
import uuid
from app.models.user import User
from flask import url_for


class TestSignUp:
    """Test cases for user registration endpoint."""

    @patch("app.services.auth.redis_client")
    @patch("app.tasks.auth.send_verification_email.delay")
    def test_successful_signup(self, send_verification_mock, redis_mock, client, app):
        """Test successful user registration."""
        # Configure Redis mock
        redis_mock.exists.return_value = False  # No existing signup
        redis_mock.setex.return_value = True  # Successful storage

        # Configure email sending mock
        send_verification_mock.return_value = None

        # Test data
        new_user = {
            "username": "newuser",
            "email": "new@test.com",
            "password": "Newuser123!",
            "name": "New User",
        }

        # Make the request
        response = client.post(url_for("auth.sign-up"), json=new_user)

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data

        # Verify redis was called
        redis_mock.exists.assert_called_once()
        redis_mock.setex.assert_called()

        # Verify email task was called
        send_verification_mock.assert_called_once()

        # Verify user wasn't added to database yet (awaiting verification)
        with app.app_context():
            user = User.query.filter_by(email="new@test.com").first()
            assert user is None

    def test_signup_existing_username(self, client, test_user):
        """Test registration with an existing username."""
        response = client.post(
            url_for("auth.sign-up"),
            json={
                "username": "testuser",  # Already exists in test data
                "email": "another@test.com",
                "password": "Another123!",
                "name": "Another User",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "username" in str(data["error"]).lower()

    def test_signup_existing_email(self, client, test_user):
        """Test registration with an existing email."""
        response = client.post(
            url_for("auth.sign-up"),
            json={
                "username": "newuser123",
                "email": "user@test.com",  # Already exists in test data
                "password": "Another123!",
                "name": "Another User",
            },
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "email" in str(data["error"]).lower()

    def test_signup_invalid_data(self, client):
        """Test signup with invalid data."""
        # Invalid username (too short)
        response1 = client.post(
            url_for("auth.sign-up"),
            json={
                "username": "ab",  # Too short
                "email": "new@test.com",
                "password": "Password",
                "name": "New User",
            },
        )

        assert response1.status_code == 400
        data1 = json.loads(response1.data)
        assert "error" in data1
        assert "username" in str(data1["error"]).lower()
