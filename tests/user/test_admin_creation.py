import uuid
from unittest.mock import patch
from app.models.user import User
from flask import url_for


class TestAdminUserResource:
    """Tests for admin user creation"""

    @patch("app.services.auth.redis_client")
    @patch("app.services.auth.send_verification_email.delay")
    def test_create_admin_user(
        self,
        send_verification_mock,
        redis_mock,
        client,
        admin_user,
        admin_headers,
        db_session,
    ):
        """Test creating an admin user (by admin)"""
        # Mock Redis operations
        verification_token = str(uuid.uuid4())
        redis_mock.exists.return_value = False  # No existing registration
        redis_mock.setex.return_value = True

        # Admin user data
        admin_data = {
            "username": "newadmin",
            "email": "newadmin@test.com",
            "password": "AdminPass123!",
            "name": "New Admin",
        }

        # Create admin user
        response = client.post(
            url_for("admin.create-admin"), json=admin_data, headers=admin_headers
        )

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "admin user registration initiated" in data["message"].lower()

        # Verify Redis operations were called
        redis_mock.exists.assert_called_once()
        redis_mock.setex.assert_called()

        # Verify email task was called
        send_verification_mock.assert_called_once()

    def test_create_admin_as_regular_user(
        self, client, test_user, auth_headers, db_session
    ):
        """Test regular user cannot create admin users"""
        # Admin user data
        admin_data = {
            "username": "newadmin",
            "email": "newadmin@test.com",
            "password": "AdminPass123!",
            "name": "New Admin",
        }

        # Try to create admin user as regular user
        response = client.post(
            url_for("admin.create-admin"), json=admin_data, headers=auth_headers
        )

        # Check response - should fail
        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data
        assert "don't have access" in str(data["error"]).lower()

        # Verify no admin user was created in the database
        admin = db_session.query(User).filter_by(email="newadmin@test.com").first()
        assert admin is None
