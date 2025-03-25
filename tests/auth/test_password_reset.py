import json
import pytest
from unittest.mock import patch
import uuid
from app.models.user import User
from flask import url_for


class TestPasswordReset:
    """Test cases for password reset request."""

    @patch("app.services.auth.redis_client")
    @patch("app.tasks.auth.send_password_reset_email.delay")
    def test_password_reset_request_success(
        self, send_email_mock, redis_mock, client, test_user
    ):
        """Test successful password reset request."""
        # Configure mocks
        redis_mock.exists.return_value = False  # No rate limiting
        redis_mock.setex.return_value = True
        send_email_mock.return_value = None

        # Make request
        response = client.post(
            url_for("auth.reset-password"), json={"email": "user@test.com"}
        )

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert (
            data["message"].lower()
            == "Check you gmail inbox, you will receive a password reset link shortly.".lower()
        )

        # Verify mocks were called
        redis_mock.exists.assert_called_once()
        send_email_mock.assert_called_once()

    def test_password_reset_missing_email(self, client):
        """Test password reset with missing email field."""
        response = client.post(url_for("auth.reset-password"), json={})

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "email" in str(data["error"]).lower()


class TestPasswordResetConfirm:
    """Test cases for confirming password reset."""

    @patch("app.utils.tokens.redis_client")
    def test_password_reset_confirm_success(
        self, redis_mock, client, test_user, db_session
    ):
        """Test successful password reset confirmation."""
        # Setup variables
        token = str(uuid.uuid4())
        user_id = str(test_user.id)

        # Configure Redis mock to return user ID when token is verified
        redis_key = f"password_reset:{token}"
        redis_mock.get.return_value = user_id
        redis_mock.delete.return_value = True

        password_data = {
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }
        response = client.post(
            url_for("auth.reset-password-confirm", token=token), json=password_data
        )
        db_session.refresh(test_user)

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["message"].lower() == "Password has been reset successfully".lower()
        assert test_user.check_password("NewPassword123!")

        # Verify Redis operations
        redis_mock.get.assert_called_once_with(redis_key)
        redis_mock.delete.assert_called_once_with(redis_key)

    @patch("app.utils.tokens.redis_client")
    def test_password_reset_confirm_invalid_token(self, redis_mock, client):
        """Test password reset confirmation with invalid token."""

        token = str(uuid.uuid4())
        redis_key = f"password_reset:{token}"
        redis_mock.get.return_value = None

        # Password data
        password_data = {
            "password": "NewPassword123!",
            "confirm_password": "NewPassword123!",
        }

        response = client.post(
            url_for("auth.reset-password-confirm", token=token), json=password_data
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert str(data["error"]).lower() == "Invalid or expired reset token".lower()

        # Verify Redis get was called but not delete
        redis_mock.get.assert_called_once_with(redis_key)
        redis_mock.delete.assert_not_called()

    def test_password_reset_confirm_mismatched_passwords(self, client):
        """Test password reset confirmation with mismatched passwords."""
        # Generate a token
        token = str(uuid.uuid4())

        # Mismatched passwords
        password_data = {
            "password": "NewPassword123!",
            "confirm_password": "DifferentPassword123!",
        }

        # Make request
        response = client.post(
            url_for("auth.reset-password-confirm", token=token), json=password_data
        )

        # Check response
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "password" in str(data["error"]).lower()
