import uuid
from unittest.mock import patch
from app.extensions import db
from app.models.user import User
from flask import url_for


class TestUserListResource:
    """Tests for listing users (admin access)"""

    def test_list_users_as_admin(self, client, test_user, admin_user, admin_headers):
        """Test admin can list all users"""
        response = client.get(url_for("user.users"), headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Check paginated response format
        assert "data" in data
        assert "total_items" in data
        assert "current_page" in data
        assert "total_pages" in data
        assert "per_page" in data

        # Verify users are returned
        users = data["data"]
        assert len(users) > 0

        # Check user properties
        user = users[0]
        assert "id" in user
        assert "username" in user
        assert "email" in user
        assert "role" in user

    def test_list_users_as_regular_user(self, client, test_user, auth_headers):
        """Test regular user cannot list all users"""
        response = client.get(url_for("user.users"), headers=auth_headers)

        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data

    def test_list_users_unauthenticated(self, client):
        """Test unauthenticated request is rejected"""
        response = client.get(url_for("user.users"))

        assert response.status_code == 401
        data = response.get_json()
        assert "error" in data


class TestUserDetailResource:
    """Tests for user detail operations (get, update, delete)"""

    def test_get_own_profile(self, client, test_user, auth_headers):
        """Test getting own user profile"""
        response = client.get(
            url_for("user.user-detail", id=test_user.id), headers=auth_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username
        assert data["email"] == test_user.email

    def test_admin_get_other_profile(
        self, client, admin_user, test_user, admin_headers
    ):
        """Test admin getting another user's profile"""
        response = client.get(
            url_for("user.user-detail", id=test_user.id), headers=admin_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(test_user.id)
        assert data["username"] == test_user.username

    def test_user_get_other_profile(self, client, test_user, admin_user, auth_headers):
        """Test user trying to get another user's profile"""
        response = client.get(
            url_for("user.user-detail", id=admin_user.id), headers=auth_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "User not found"

    def test_admin_get_child_user_profile(self, client, child_user, admin_headers):
        """Test admin getting a child user's profile"""
        response = client.get(
            url_for("user.user-detail", id=child_user.id), headers=admin_headers
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["id"] == str(child_user.id)
        assert data["username"] == child_user.username

    def test_child_user_get_parent_profile(self, client, test_user, child_headers):
        """Test child user getting parent user's profile"""
        response = client.get(
            url_for("user.user-detail", id=test_user.id), headers=child_headers
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert data["error"] == "User not found"

    def test_get_nonexistent_profile(self, client, test_user, auth_headers):
        """Test getting nonexistent profile"""
        fake_id = uuid.uuid4()
        response = client.get(
            url_for("user.user-detail", id=fake_id), headers=auth_headers
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_update_user_profile_success(self, client, test_user, auth_headers):
        """Test successful profile update"""
        # Update data
        update_data = {"name": "Updated Name", "gender": "MALE"}

        # Make request
        response = client.patch(
            url_for("user.user-detail", id=test_user.id),
            json=update_data,
            headers=auth_headers,
        )

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Updated Name"
        assert data["gender"] == "MALE"

        # Verify database update
        with client.application.app_context():
            updated_user = db.session.get(User, test_user.id)
            assert updated_user.name == "Updated Name"
            assert updated_user.gender.value == "MALE"

    def test_update_username_validation(
        self, client, test_user, admin_user, auth_headers
    ):
        """Test username validation during update"""
        # Try to update to admin's username
        update_data = {"username": admin_user.username}

        response = client.patch(
            url_for("user.user-detail", id=test_user.id),
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "username" in str(data["error"]).lower()

    def test_admin_update_user_profile(
        self, client, admin_headers, test_user, db_session
    ):
        """Test admin updating another user's profile"""
        update_data = {"name": "Admin Updated User", "date_of_birth": "2000-10-11"}

        response = client.patch(
            url_for("user.user-detail", id=test_user.id),
            json=update_data,
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"] == "Admin Updated User"
        assert data["date_of_birth"] == "2000-10-11"

        db_session.refresh(test_user)
        assert test_user.name == "Admin Updated User"
        assert str(test_user.date_of_birth) == "2000-10-11"

    def test_parent_update_child_profile(self, client, child_user, auth_headers):
        """Test parent updating child user's profile"""
        update_data = {"name": "Parent Updated Child", "date_of_birth": "2000-10-11"}

        response = client.patch(
            url_for("user.user-detail", id=child_user.id),
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data
        assert "don't have permission" in data["error"].lower()

    @patch("app.resources.user.delete_user_account")
    @patch("app.tasks.user.soft_delete_user_related_objects.delay")
    def test_delete_user_account(
        self, delete_task_mock, delete_user_mock, client, test_user, auth_headers
    ):
        """Test deleting own user account"""
        # Mock delete_user_account to avoid actually deleting
        delete_user_mock.return_value = True
        delete_user_mock.return_value = True

        # Delete request with password
        response = client.delete(
            url_for("user.user-detail", id=test_user.id),
            json={"password": "Password123!"},
            headers=auth_headers,
        )
        assert response.status_code == 204

        # Verify mocks were called
        delete_user_mock.assert_called_once()

    def test_delete_without_password(self, client, test_user, auth_headers):
        """Test deleting account without providing password"""
        # Delete request without password
        response = client.delete(
            url_for("user.user-detail", id=test_user.id), json={}, headers=auth_headers
        )

        # Check response - should fail
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "password" in str(data["error"]).lower()

    @patch("app.services.user.soft_delete_user_related_objects.delay")
    def test_admin_delete_other_user(
        self, delete_task_mock, client, admin_headers, test_user, db_session
    ):
        """Test admin deleting another user's account"""
        # Mock delete functions
        delete_task_mock.return_value = True

        # Admin should be able to delete without password
        response = client.delete(
            url_for("user.user-detail", id=test_user.id), json={}, headers=admin_headers
        )
        assert response.status_code == 204
        db_session.refresh(test_user)
        assert test_user.is_deleted

        delete_task_mock.assert_called_once()

    def test_admin_delete_nonexistent_user(self, client, admin_headers):
        """Test admin deleting a nonexistent user"""
        # Try to delete nonexistent user
        fake_id = uuid.uuid4()
        response = client.delete(
            url_for("user.user-detail", id=fake_id), headers=admin_headers
        )

        # Should return 404 Not Found
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_user_delete_other_user(self, client, test_user, admin_user, auth_headers):
        """Test user trying to delete another user's account"""
        # Regular user trying to delete admin account
        response = client.delete(
            url_for("user.user-detail", id=admin_user.id),
            json={"password": "Password123!"},
            headers=auth_headers,
        )

        # Should fail with 404 (user not found)
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_parent_delete_child_user(
        self,
        client,
        auth_headers,
        child_user,
    ):
        """Test parent trying to delete child user account"""
        # Parent trying to delete child account
        response = client.delete(
            url_for("user.user-detail", id=child_user.id),
            json={},
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data

    def test_child_delete_parent_user(self, client, test_user, child_headers):
        """Test child trying to delete parent user account"""
        # Child trying to delete parent account
        response = client.delete(
            url_for("user.user-detail", id=test_user.id),
            json={},
            headers=child_headers,
        )

        # Should fail with 404
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_delete_with_incorrect_password(self, client, test_user, auth_headers):
        """Test deleting account with incorrect password"""
        response = client.delete(
            url_for("user.user-detail", id=test_user.id),
            json={"password": "WrongPassword123!"},
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "password" in str(data["error"]).lower()

    @patch("app.tasks.user.soft_delete_user_related_objects.delay")
    def test_admin_delete_admin_user(
        self, delete_task_mock, client, admin_user, admin_headers, db_session
    ):
        """Test admin attempting to delete another admin account"""
        # Create another admin user
        from app.models.user import User, UserRole

        another_admin = User(
            username="admin2",
            email="admin2@example.com",
            password="SecurePass123!",
            name="Another Admin",
            role=UserRole.ADMIN,
        )
        db_session.add(another_admin)
        db_session.commit()
        admin_id = another_admin.id

        # Mock delete functions
        delete_task_mock.return_value = True

        # Admin deleting another admin
        response = client.delete(
            url_for("user.user-detail", id=admin_id), json={}, headers=admin_headers
        )

        # Check if your API allows this
        assert response.status_code == 204

        db_session.refresh(another_admin)
        assert another_admin.is_deleted
        delete_task_mock.assert_called_once()

        # clean up
        db_session.delete(another_admin)
        db_session.commit()
        db_session.close()
