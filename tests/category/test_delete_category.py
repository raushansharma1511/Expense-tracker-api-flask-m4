from app.models.user import User
from app.models.category import Category
from app.models.budget import Budget
from datetime import datetime
from flask import url_for


class TestCategoryDelete:
    """Tests for category detail operations (get, update, delete)"""

    def test_delete_own_category_success(
        self, client, user_category, auth_headers, db_session
    ):
        """Test user deleting their own category (soft delete)"""
        response = client.delete(
            url_for("category.category-detail", id=user_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 204

        # Ensure category is soft-deleted
        db_session.refresh(user_category)
        assert user_category.is_deleted is True

    def test_user_delete_predefined_category(
        self, client, predefined_category, auth_headers
    ):
        """Test user attempting to delete predefined category (should fail)"""
        response = client.delete(
            url_for("category.category-detail", id=predefined_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_admin_delete_predefined_category(
        self, client, predefined_category, admin_headers, db_session
    ):
        """Test admin deleting predefined category"""
        response = client.delete(
            url_for("category.category-detail", id=predefined_category.id),
            headers=admin_headers,
        )
        assert response.status_code == 204

        # Ensure category is soft-deleted
        db_session.refresh(predefined_category)
        assert predefined_category.is_deleted is True

    def test_admin_delete_user_category(
        self, client, user_category, admin_headers, db_session
    ):
        """Test admin deleting user's category"""
        # Mock the DB query to return no references
        response = client.delete(
            url_for("category.category-detail", id=user_category.id),
            headers=admin_headers,
        )

        assert response.status_code == 204
        db_session.refresh(user_category)
        assert user_category.is_deleted is True

    def test_user_delete_other_user_category(self, client, auth_headers, db_session):
        """Test user deleting another user's category (should fail)"""
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

        response = client.delete(
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

    def test_parent_delete_child_category(
        self, client, test_user, child_category, auth_headers
    ):
        """Test parent attempting to delete child's category (should fail)"""
        response = client.delete(
            url_for("category.category-detail", id=child_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data

    def test_delete_with_references(
        self, client, user_category, auth_headers, db_session
    ):
        """Test deleting a category that has references (should fail)"""
        # Create a budget that references this category
        budget = Budget(
            user_id=user_category.user_id,
            category_id=user_category.id,
            amount=100.00,
            month=datetime.now().month,
            year=datetime.now().year,
        )
        db_session.add(budget)
        db_session.commit()

        response = client.delete(
            url_for("category.category-detail", id=user_category.id),
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert (
            data["error"].lower()
            == "Cannot delete category with existing transactions, recurring transactions, or budgets.".lower()
        )

        db_session.delete(budget)
        db_session.commit()

    def test_delete_already_deleted_category(
        self, client, test_user, auth_headers, db_session
    ):
        """Test attempting to delete an already deleted category"""
        # Create a category that's already deleted
        deleted_category = Category(
            name="Already Deleted Category",
            user_id=test_user.id,
            is_predefined=False,
            is_deleted=True,  # Already deleted
        )
        db_session.add(deleted_category)
        db_session.commit()
        category_id = deleted_category.id

        response = client.delete(
            url_for("category.category-detail", id=category_id),
            headers=auth_headers,
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data
        assert "not found" in data["error"].lower()

        # Clean up
        db_session.delete(deleted_category)
        db_session.commit()
