from flask import url_for
import pytest
import uuid
from app.models.category import Category


class TestBudgetDetailResource:

    @pytest.fixture(autouse=True)
    def mock_check_budget_thresholds(self, mocker):
        """
        Mock the check_budget_thresholds.delay call for all tests in this class.
        """
        mock = mocker.patch("app.services.budget.check_budget_thresholds.delay")
        mock.return_value = None
        return mock

    def test_update_own_budget(
        self, client, test_user, user_budget, auth_headers, db_session
    ):
        category2 = Category(name="Test Category 2", user_id=test_user.id)
        db_session.add(category2)
        db_session.commit()
        db_session.refresh(category2)
        update_data = {"amount": "150.00", "category_id": category2.id}
        response = client.patch(
            url_for("budget.budget-detail", id=user_budget.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert data["amount"] == "150.00"

    def test_update_child_budget_by_parent(self, client, child_budget, auth_headers):
        update_data = {"amount": "75.00"}
        response = client.patch(
            url_for("budget.budget-detail", id=child_budget.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 403
        assert "error" in response.get_json()
        assert (
            "You don't have permission to modify your child resource"
            in response.get_json()["error"]
        )

    def test_update_other_user_budget(
        self, client, test_user2, user_budget, auth_headers_user2
    ):
        update_data = {"amount": "75.00"}
        response = client.patch(
            url_for("budget.budget-detail", id=user_budget.id),
            json=update_data,
            headers=auth_headers_user2,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "Budget not found" in response.get_json()["error"]

    def test_update_budget_as_admin(self, client, child_budget, admin_headers):
        update_data = {"amount": "75.00"}
        response = client.patch(
            url_for("budget.budget-detail", id=child_budget.id),
            json=update_data,
            headers=admin_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert data["amount"] == "75.00"

    def test_update_budget_invalid_amount(self, client, user_budget, auth_headers):
        update_data = {"amount": "-10.00"}
        response = client.patch(
            url_for("budget.budget-detail", id=user_budget.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "Must be greater than or equal to 1 and less than or equal to 99999999.99"
            in response.get_json()["error"]["amount"]
        )

    def test_update_budget_invalid_data(self, client, user_budget, auth_headers):
        update_data = {"category_id": uuid.uuid4()}
        response = client.patch(
            url_for("budget.budget-detail", id=user_budget.id),
            json=update_data,
            headers=auth_headers,
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
