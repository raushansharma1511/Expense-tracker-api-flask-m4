import uuid
from unittest.mock import patch
from app.models.user import ParentChildRelation
from flask import url_for


class TestChildUserResource:
    """Tests for child user management"""

    @patch("app.services.auth.redis_client")
    @patch("app.services.auth.send_verification_email.delay")
    def test_create_child_user(
        self,
        send_verification_mock,
        redis_mock,
        client,
        test_user,
        auth_headers,
        db_session,
    ):
        """Test creating a child user"""
        # Mock Redis operations
        verification_token = str(uuid.uuid4())
        redis_mock.exists.return_value = False
        redis_mock.setex.return_value = True

        send_verification_mock.return_value = None

        # Child user data
        child_data = {
            "username": "childuser",
            "email": "child@test.com",
            "password": "ChildPass123!",
            "name": "Child User",
        }

        # Create child user
        response = client.post(
            url_for("user.child-user", id=test_user.id),
            json=child_data,
            headers=auth_headers,
        )

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data
        assert "child user registration initiated" in data["message"].lower()

        # Verify redis was called
        redis_mock.exists.assert_called_once()
        redis_mock.setex.assert_called()

        # Verify email task was called
        send_verification_mock.assert_called_once()

    def test_get_child_user(
        self, client, test_user, child_user, auth_headers, db_session
    ):
        """Test getting child user"""
        # Now get the child user
        response = client.get(
            url_for("user.child-user", id=test_user.id), headers=auth_headers
        )

        # Check response
        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert data["role"] == "CHILD_USER"

        # Check fields match the child_user fixture
        assert data["id"] == str(child_user.id)
        assert data["username"] == child_user.username
        assert data["email"] == child_user.email
        relation = ParentChildRelation.query.filter_by(child_id=child_user.id).first()
        assert relation is not None and relation.parent_id == test_user.id

    def test_create_child_when_already_has_child(
        self, client, test_user, child_user, auth_headers, db_session
    ):
        """Test trying to create a child user when parent already has one"""
        # The child_user fixture has already created a child for test_user

        # Try to create another child
        child_data = {
            "username": "anotherchild",
            "email": "another.child@test.com",
            "password": "ChildPass123!",
            "name": "Another Child",
        }

        response = client.post(
            url_for("user.child-user", id=test_user.id),
            json=child_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert (
            str(data["error"]).lower()
            == "a child user already exists for this user".lower()
        )
