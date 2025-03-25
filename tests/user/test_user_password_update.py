import pytest
from app.models.user import User
from app.extensions import db
from flask import url_for


class TestPasswordUpdateResource:
    """Tests for password update functionality"""

    def test_password_update_success(self, client, test_user, auth_headers):
        """Test successful password update"""
        # Store original password hash
        original_hash = test_user.password

        password_data = {
            "current_password": "Password123!",
            "new_password": "NewPassword456!",
            "confirm_password": "NewPassword456!",
        }
        response = client.post(
            url_for("user.update-password", id=test_user.id),
            json=password_data,
            headers=auth_headers,
        )

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "password updated" in data["message"].lower()

        # Verify password was updated in database
        with client.application.app_context():
            updated_user = db.session.get(User, test_user.id)
            assert updated_user.password != original_hash
            assert updated_user.check_password("NewPassword456!")

    @pytest.mark.parametrize(
        "password_data,error_field",
        [
            # Wrong current password
            (
                {
                    "current_password": "WrongPassword123!",
                    "new_password": "NewPassword456!",
                    "confirm_password": "NewPassword456!",
                },
                "current_password",
            ),
            # Passwords don't match
            (
                {
                    "current_password": "Password123!",
                    "new_password": "NewPassword456!",
                    "confirm_password": "DifferentPassword789!",
                },
                "confirm_password",
            ),
            # Weak password
            (
                {
                    "current_password": "Password123!",
                    "new_password": "weak",
                    "confirm_password": "weak",
                },
                "new_password",
            ),
        ],
    )
    def test_password_update_validation(
        self, client, test_user, auth_headers, password_data, error_field
    ):
        """Test password update validation"""
        # Update password with invalid data
        response = client.post(
            url_for("user.update-password", id=test_user.id),
            json=password_data,
            headers=auth_headers,
        )

        # Check validation error
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert error_field in str(data["error"]).lower()
