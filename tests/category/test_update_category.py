from app.models.user import User
from app.models.category import Category
from flask import url_for


class TestCategoryUpdate:
    """Tests for category detail operations (get, update, delete)"""

    def test_update_own_category(
        self, client, test_user, user_category, auth_headers, db_session
    ):
        """Test user updating their own category"""
        update_data = {"name": "Updated Category Name"}

        response = client.patch(
            url_for("category.category-detail", id=user_category.id),
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"].lower() == "Updated Category Name".lower()

        # Verify database update
        db_session.refresh(user_category)
        assert user_category.name.lower() == "Updated Category Name".lower()

    def test_user_update_predefined_category(
        self, client, test_user, predefined_category, auth_headers
    ):
        """Test regular user updating predefined category (should fail)"""
        update_data = {"name": "Attempted Update"}

        response = client.patch(
            url_for("category.category-detail", id=predefined_category.id),
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_admin_update_predefined_category(
        self, client, predefined_category, admin_headers, db_session
    ):
        """Test admin updating predefined category"""
        update_data = {"name": "Admin Updated Category"}

        response = client.patch(
            url_for("category.category-detail", id=predefined_category.id),
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["name"].lower() == "Admin Updated Category".lower()

        # Verify database update
        db_session.refresh(predefined_category)
        assert predefined_category.name.lower() == "Admin Updated Category".lower()

    def test_admin_update_user_category(
        self, client, user_category, admin_headers, db_session
    ):
        """Test admin updating regular user's category"""
        update_data = {"name": "Admin Changed User Category"}

        response = client.patch(
            url_for("category.category-detail", id=user_category.id),
            json=update_data,
            headers=admin_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert data["name"].lower() == "Admin Changed User Category".lower()

        # Verify database update
        db_session.refresh(user_category)
        assert user_category.name.lower() == "Admin Changed User Category".lower()

    def test_update_other_user_category(self, client, auth_headers, db_session):
        """Test user updating another user's category (should fail)"""
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

        response = client.patch(
            url_for("category.category-detail", id=new_category.id),
            json={"name": "Attempted Update"},
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

    def test_parent_update_child_category(self, client, child_category, auth_headers):
        """Test parent updating child's category (should fail)"""
        update_data = {"name": "Parent Changed Child Category"}

        response = client.patch(
            url_for("category.category-detail", id=child_category.id),
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 403
        data = response.get_json()
        assert "error" in data

    def test_child_update_parent_category(self, client, user_category, child_headers):
        """Test child updating parent's category (should fail)"""
        update_data = {"name": "Child Changed Parent Category"}

        response = client.patch(
            url_for("category.category-detail", id=user_category.id),
            json=update_data,
            headers=child_headers,
        )

        assert response.status_code == 404
        data = response.get_json()
        assert "error" in data

    def test_invalid_update_data(self, client, user_category, auth_headers):
        """Test updating a category with invalid data"""
        # Test with empty name
        empty_name = {"name": ""}

        response = client.patch(
            url_for("category.category-detail", id=user_category.id),
            json=empty_name,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "name" in str(data["error"]).lower()

    def test_update_category_to_duplicate_name(
        self, client, test_user, user_category, auth_headers, db_session
    ):
        """Test updating a category to a name that already exists for the user"""
        # Create a second category for the same user
        second_category = Category(
            name="Second test tategory", user_id=test_user.id, is_predefined=False
        )
        db_session.add(second_category)
        db_session.commit()
        db_session.refresh(second_category)

        update_data = {"name": second_category.name}

        response = client.patch(
            url_for("category.category-detail", id=user_category.id),
            json=update_data,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "already exists" in data["error"].get("name").lower()

        # Clean up
        db_session.delete(second_category)
        db_session.commit()
