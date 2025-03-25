import json
import uuid
from app.models.category import Category
from flask import url_for


class TestCategoryListResource:
    """Tests for category listing and creation"""

    def test_list_categories_as_admin(
        self,
        client,
        admin_user,
        admin_headers,
        predefined_category,
        user_category,
    ):
        """Test admin can list all categories"""
        response = client.get(url_for("category.categories"), headers=admin_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Check pagination data structure
        assert "data" in data
        assert "total_items" in data
        assert "current_page" in data
        assert "total_pages" in data
        assert "per_page" in data

        # Check categories are returned
        categories = data["data"]
        assert len(categories) >= 2

        # Find our test categories in the results
        predefined_found = False
        user_cat_found = False

        for cat in categories:
            if cat["id"] == str(predefined_category.id):
                predefined_found = True
                assert cat["is_predefined"] is True

            if cat["id"] == str(user_category.id):
                user_cat_found = True
                assert cat["is_predefined"] is False
                assert cat["user_id"] == str(user_category.user_id)

        assert predefined_found and user_cat_found

    def test_list_categories_as_regular_user(
        self,
        client,
        test_user,
        auth_headers,
        predefined_category,
        user_category,
        child_category,
    ):
        """Test regular user can list predefined categories and their own"""
        response = client.get(url_for("category.categories"), headers=auth_headers)

        assert response.status_code == 200
        data = response.get_json()

        # Check categories are returned
        categories = data["data"]
        assert len(categories) >= 2  # At least predefined + own

        # Find our test categories in the results
        predefined_found = False
        user_cat_found = False
        child_cat_found = False

        for cat in categories:
            if cat["id"] == str(predefined_category.id):
                predefined_found = True
                assert cat["is_predefined"] is True

            if cat["id"] == str(user_category.id):
                user_cat_found = True
                assert cat["is_predefined"] is False
                assert cat["user_id"] == str(test_user.id)

            if cat["id"] == str(child_category.id):
                child_cat_found = True

        # Should see predefined and own categories, but NOT child's categories
        assert predefined_found and user_cat_found and not child_cat_found

    def test_list_child_categories_by_parent(
        self, client, test_user, auth_headers, child_user, child_category
    ):
        """Test parent can list child's categories"""
        response = client.get(
            f"{url_for('category.categories')}?child_id={child_user.id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data

        # Check categories are returned
        categories = data["data"]
        assert len(categories) >= 1  # At least the child category

        # Find child category in results
        child_cat_found = False
        for cat in categories:
            if cat["id"] == str(child_category.id):
                child_cat_found = True
                assert cat["user_id"] == str(child_user.id)

        assert child_cat_found

    def test_list_categories_as_child_user(
        self, client, child_headers, child_user, predefined_category, child_category
    ):
        """Test child user can list predefined categories and their own"""
        response = client.get(url_for("category.categories"), headers=child_headers)

        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data

        categories = data["data"]

        # Find predefined and child categories
        predefined_found = False
        child_cat_found = False

        for cat in categories:
            if cat["id"] == str(predefined_category.id):
                predefined_found = True
                assert cat["is_predefined"] is True

            if cat["id"] == str(child_category.id):
                child_cat_found = True
                assert cat["user_id"] == str(child_user.id)

        assert predefined_found  # Should see predefined categories
        assert child_cat_found  # Should see own categories

    def test_create_category_success(self, client, test_user, auth_headers, db_session):
        """Test creating a new category as regular user"""
        new_category = {"name": "New Test Category", "user_id": str(test_user.id)}

        response = client.post(
            url_for("category.categories"), json=new_category, headers=auth_headers
        )

        assert response.status_code == 201
        data = response.get_json()

        # Check response data
        assert data["name"].lower() == "New Test Category".lower()
        assert data["user_id"] == str(test_user.id)
        assert data["is_predefined"] is False

        # Verify category was created in database
        created_category = (
            db_session.query(Category).filter_by(id=uuid.UUID(data["id"])).first()
        )
        assert created_category is not None
        assert created_category.name.lower() == "New Test Category".lower()

        # Clean up
        db_session.delete(created_category)
        db_session.commit()

    def test_create_predefined_category(
        self, client, admin_user, admin_headers, db_session
    ):
        """Test admin creating a predefined category"""
        new_category = {
            "name": "New Predefined Category",
            "user_id": str(admin_user.id),
        }

        response = client.post(
            url_for("category.categories"), json=new_category, headers=admin_headers
        )

        assert response.status_code == 201
        data = response.get_json()

        # Check response data - should be predefined since created by admin
        assert data["name"].lower() == "New Predefined Category".lower()
        assert data["user_id"] == str(admin_user.id)
        assert data["is_predefined"] is True

        # Verify category was created in database
        created_category = (
            db_session.query(Category).filter_by(id=uuid.UUID(data["id"])).first()
        )
        assert created_category is not None
        assert created_category.is_predefined is True

        # Clean up
        db_session.delete(created_category)
        db_session.commit()

    def test_user_attempt_create_category_for_others(
        self, client, test_user, child_user, auth_headers
    ):
        """Test regular user attempting to create category for others (should fail)"""
        # Try to create for child user
        new_category = {
            "name": "Invalid Category",
            "user_id": str(child_user.id),  # Different user
        }

        response = client.post(
            url_for("category.categories"), json=new_category, headers=auth_headers
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "create categories for yourself only" in str(data["error"]).lower()

    def test_admin_create_category_for_others(
        self, client, admin_headers, test_user, db_session
    ):
        """Test admin creating category for others (should work)"""
        new_category = {
            "name": "Regular User Category",
            "user_id": str(test_user.id),  # Creating for regular user
        }

        response = client.post(
            url_for("category.categories"), json=new_category, headers=admin_headers
        )

        assert response.status_code == 201
        data = response.get_json()

        # Check response data - should NOT be predefined since for regular user
        assert data["name"].lower() == "Regular User Category".lower()
        assert data["user_id"] == str(test_user.id)
        assert data["is_predefined"] is False

        # Clean up
        created_category = (
            db_session.query(Category).filter_by(id=uuid.UUID(data["id"])).first()
        )
        db_session.delete(created_category)
        db_session.commit()

    def test_create_category_name_missing(self, client, test_user, auth_headers):
        """Test validation when creating a category"""
        # Test with missing name
        missing_name = {"user_id": str(test_user.id)}

        response = client.post(
            url_for("category.categories"),
            json=missing_name,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "name" in data["error"]

    def test_create_category_name_empty(self, client, test_user, auth_headers):
        """Test validation when creating a category"""
        # Test with empty name
        empty_name = {"name": "", "user_id": str(test_user.id)}

        response = client.post(
            url_for("category.categories"),
            json=empty_name,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "name" in data["error"]

    def test_create_category_user_id_missing(self, client, auth_headers):
        """Test validation when creating a category"""
        # Test with missing user_id
        missing_user_id = {"name": "Test Category"}

        response = client.post(
            url_for("category.categories"),
            json=missing_user_id,
            headers=auth_headers,
        )

        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data
        assert "user_id" in data["error"]
