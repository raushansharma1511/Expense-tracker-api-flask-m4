import uuid
from unittest.mock import patch
from flask import url_for


class TestEmailChangeResource:
    """Tests for email change functionality"""

    @patch("app.services.user.redis_client")
    @patch("app.services.user.send_email_change_otps.delay")
    def test_request_email_change_self(
        self, send_email_mock, redis_client_mock, client, test_user, auth_headers
    ):
        """Test requesting email change for self (OTP flow)"""
        # Email change request
        redis_client_mock.exists.return_value = (
            False  # No existing request (rate limit)
        )
        redis_client_mock.setex.return_value = True  # Successful OTP storage
        redis_client_mock.ttl.return_value = 900

        send_email_mock.return_value = True

        response = client.post(
            url_for("user.update-email", id=test_user.id),
            json={"new_email": "newemail@test.com"},
            headers=auth_headers,
        )
        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert (
            data["message"].lower()
            == "Enter the otps sent to your current and new email addresses".lower()
        )

        # Verify Redis interactions
        redis_client_mock.exists.assert_called_once()
        redis_client_mock.setex.assert_called_once()

        # Verify Celery task was called
        send_email_mock.assert_called_once()

    @patch("app.services.user.redis_client")
    @patch("app.resources.user.send_admin_email_change_verification.delay")
    def test_admin_request_email_change_for_other(
        self,
        send_verification_mock,
        redis_client_mock,
        client,
        admin_user,
        test_user,
        admin_headers,
    ):
        """Test admin requesting email change for another user (token flow)"""
        redis_client_mock.exists.return_value = False  # No rate limit
        redis_client_mock.get.return_value = None  # No previous token
        redis_client_mock.setex.return_value = True  # Successful token storage

        # Mock Celery task
        send_verification_mock.return_value = True

        new_email = "changedbyadmin@test.com"

        response = client.post(
            url_for("user.update-email", id=test_user.id),
            json={"new_email": new_email},
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert (
            data["message"].lower()
            == f"Verification link sent to {new_email}. User must click the link to confirm email change.".lower()
        )

        redis_client_mock.exists.assert_called_once()
        redis_client_mock.get.assert_called_once()
        assert redis_client_mock.setex.call_count == 3  # Token and rate limit

        # Verify Celery task
        send_verification_mock.assert_called_once()

    def test_email_change_validation(self, client, test_user, admin_user, auth_headers):
        """Test email change validation (email already exists)"""
        # Try to change to an existing email
        response = client.post(
            url_for("user.update-email", id=test_user.id),
            json={"new_email": admin_user.email},
            headers=auth_headers,
        )

        # Check validation error
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "new_email" in data["error"]


class TestEmailChangeConfirmation:
    """Tests for confirming email changes"""

    @patch("app.services.user.redis_client")
    def test_confirm_email_change_success(
        self, redis_mock, client, test_user, auth_headers, db_session
    ):
        """Test successful email change confirmation with OTPs"""
        # Configure Redis mock to return stored OTPs
        redis_mock.get.return_value = (
            "newemail@test.com:current_email_otp:new_email_otp"
        )
        redis_mock.delete.return_value = True

        response = client.post(
            url_for("user.update-email-confirm", id=test_user.id),
            json={
                "current_email_otp": "current_email_otp",
                "new_email_otp": "new_email_otp",
            },
            headers=auth_headers,
        )

        db_session.refresh(test_user)

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert test_user.email == "newemail@test.com"

        redis_mock.get.assert_called_once()
        redis_mock.delete.assert_called_once()

    @patch("app.services.user.redis_client")
    def test_confirm_email_change_invalid_otp(
        self, redis_mock, client, test_user, auth_headers, db_session
    ):
        """Test email change confirmation with invalid OTP"""
        # Configure Redis mock to return stored OTPs
        redis_key = f"email_change:{test_user.id}"
        redis_mock.get.return_value = "newemail@test.com:correct_otp:correct_otp"

        # Confirm with wrong OTP
        response = client.post(
            url_for("user.update-email-confirm", id=test_user.id),
            json={"current_email_otp": "wrong_otp", "new_email_otp": "wrong_otp"},
            headers=auth_headers,
        )

        # Check response
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"].lower()
            == "Both current and new email OTPs are incorrect.".lower()
        )

        redis_mock.get.assert_called_once_with(redis_key)


class TestEmailChangeVerifyToken:
    """Tests for verifying email change token (admin-initiated flow)"""

    @patch("app.services.user.redis_client")
    def test_verify_email_change_token_success(
        self, redis_mock, client, test_user, db_session
    ):
        """Test successful email change token verification"""
        # Setup variables
        token = str(uuid.uuid4())
        user_id = str(test_user.id)
        new_email = "newemail@example.com"

        # Configure Redis mock to return token data
        redis_key = f"admin_email_change:{token}"
        redis_mock.get.return_value = f"{user_id}:{new_email}"
        redis_mock.delete.return_value = True

        response = client.get(url_for("user.verify-email", token=token))

        db_session.refresh(test_user)

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert data["message"].lower() == "Email address updated successfully".lower()

        # Verify the user's email was updated in the database
        assert test_user.email == new_email

        # Verify Redis operations occurred
        redis_mock.get.assert_called_once_with(redis_key)
        redis_mock.delete.assert_called()

    @patch("app.services.user.redis_client")
    def test_verify_email_change_token_invalid(self, redis_mock, client):
        """Test invalid email change token verification"""
        # Setup Redis mock to return None (invalid token)
        token = str(uuid.uuid4())
        redis_key = f"admin_email_change:{token}"
        redis_mock.get.return_value = None

        # Verify token
        response = client.get(url_for("user.verify-email", token=token))

        # Check response
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "invalid" in str(data["error"]).lower()

        # Verify Redis get was called (but not delete, since token was invalid)
        redis_mock.get.assert_called_once_with(redis_key)
        redis_mock.delete.assert_not_called()
