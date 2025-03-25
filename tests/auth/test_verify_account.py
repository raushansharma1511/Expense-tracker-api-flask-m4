import json
import pytest
from unittest.mock import patch
import uuid
from app.models.user import User
from flask import url_for


class TestVerifyUser:
    """Test cases for user verification endpoint."""

    @patch("app.services.auth.redis_client")
    def test_verify_user_success(self, redis_mock, client, app):
        """Test successful user verification."""
        # Generate verification token
        token = str(uuid.uuid4())
        verification_key = f"verification_token:{token}"

        # User data to be verified
        user_data = {
            "username": "verifyuser",
            "email": "verify@test.com",
            "password": "Password123!",
            "name": "Verify User",
            "role": "USER",
            "is_verified": False,
        }

        # Mock Redis to properly return the user data
        redis_mock.get.return_value = json.dumps(user_data)

        # Make verification request
        response = client.get(url_for("auth.verify-user", token=token))

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "verified successfully" in data["message"].lower()

        # Verify Redis was accessed and cleanup occurred
        redis_mock.get.assert_called_with(verification_key)
        redis_mock.delete.assert_called()

        # Verify a user was created in the database
        with app.app_context():
            user = User.query.filter_by(email="verify@test.com").first()
            assert user is not None
            assert user.username == "verifyuser"
            assert user.is_verified is True

    @patch("app.services.auth.redis_client")
    def test_verify_user_invalid_token(self, redis_mock, client):
        """Test verification with invalid token."""
        # Mock Redis to indicate token doesn't exist
        redis_mock.get.return_value = None

        # Make verification request with random token
        token = str(uuid.uuid4())
        response = client.get(url_for("auth.verify-user", token=token))

        # Check response
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "invalid or expired token" in str(data["error"]).lower()
