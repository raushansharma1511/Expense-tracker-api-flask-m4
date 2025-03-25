from app.models.user import User
from app.models.category import Category
from flask import url_for


class TestCategoryGet:
    """Tests for category detail operations (get, update, delete)"""

    def test_get_category_by_owner(
        self, client, test_user, user_category, auth_headers
    ):
        """Test getting a category by its owner"""
        response = client.get(
            url_for("category.category-detail", id=user_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()

        # Check response data
        assert data["id"] == str(user_category.id)
        assert data["name"] == user_category.name
        assert data["user_id"] == str(test_user.id)

    def test_get_predefined_category_by_user(
        self, client, test_user, predefined_category, auth_headers
    ):
        """Test getting a predefined category by regular user"""
        response = client.get(
            url_for("category.category-detail", id=predefined_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()

        # Check response data
        assert data["id"] == str(predefined_category.id)
        assert data["name"] == predefined_category.name
        assert data["is_predefined"] is True

    def test_get_user_category_by_other_user(
        self, client, test_user, auth_headers, db_session
    ):
        """Test getting a user category by another user"""
        # Create a new user
        new_user = User(
            username="newuser",
            email="newuser@test.com",
            password="NewUserPass123!",
            name="New User",
        )
        db_session.add(new_user)
        db_session.commit()
        db_session.refresh(new_user)

        # Create a category for the new user
        new_category = Category(name="New user category", user_id=new_user.id)
        db_session.add(new_category)
        db_session.commit()
        db_session.refresh(new_category)

        # Attempt to get the new user's category
        response = client.get(
            url_for("category.category-detail", id=new_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert "not found" in data["error"].lower()

        # Clean up
        db_session.delete(new_category)
        db_session.delete(new_user)
        db_session.commit()

    def test_get_child_category_by_parent(
        self, client, test_user, child_category, auth_headers
    ):
        """Test getting a child's category by parent"""
        response = client.get(
            url_for("category.category-detail", id=child_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()

        # Check response data
        assert data["id"] == str(child_category.id)
        assert data["name"] == child_category.name

    def test_get_parent_category_by_child(
        self, client, child_user, user_category, child_headers, db_session
    ):
        """Test child user trying to access parent's category (should fail)"""
        # Child trying to access parent's category
        response = client.get(
            url_for("category.category-detail", id=user_category.id),
            headers=child_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert "not found" in data["error"].lower()
