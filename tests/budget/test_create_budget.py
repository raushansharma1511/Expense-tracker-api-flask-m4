from flask import url_for
import pytest


class TestBudgetListResource:

    @pytest.fixture(autouse=True)
    def mock_check_budget_thresholds(self, mocker):
        """
        Mock the check_budget_thresholds.delay call for all tests in this class.
        """
        mock = mocker.patch("app.services.budget.check_budget_thresholds.delay")
        mock.return_value = None
        return mock

    def test_create_budget_success(
        self, client, auth_headers, budget_data, user_transaction
    ):
        response = client.post(
            url_for("budget.budgets"), json=budget_data, headers=auth_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert data["spent_amount"] == "50.00"
        assert data["amount"] == "100.00"

    def test_create_budget_as_admin(
        self, client, admin_headers, child_user, child_category
    ):
        budget_data = {
            "user_id": str(child_user.id),
            "category_id": str(child_category.id),
            "amount": "75.00",
            "month": 3,
            "year": 2025,
        }
        response = client.post(
            url_for("budget.budgets"), json=budget_data, headers=admin_headers
        )
        assert response.status_code == 201
        data = response.get_json()
        assert "id" in data
        assert data["user_id"] == str(child_user.id)

    def test_create_budget_invalid_amount(self, client, auth_headers, budget_data):
        budget_data["amount"] = "-10.00"
        response = client.post(
            url_for("budget.budgets"), json=budget_data, headers=auth_headers
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "Must be greater than or equal to 1 and less than or equal to 99999999.99"
            in response.get_json()["error"]["amount"]
        )

    def test_create_budget_missing_field(self, client, auth_headers, budget_data):
        del budget_data["month"]
        response = client.post(
            url_for("budget.budgets"), json=budget_data, headers=auth_headers
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "Missing data for required field." in response.get_json()["error"]["month"]
        )

    def test_create_budget_duplicate(
        self, client, auth_headers, budget_data, user_budget
    ):
        response = client.post(
            url_for("budget.budgets"), json=budget_data, headers=auth_headers
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "A budget already exists for this user, category, month and year"
            in response.get_json()["error"]["month_year"]
        )

    def test_create_budget_unauthenticated(self, client, budget_data):
        response = client.post(url_for("budget.budgets"), json=budget_data)
        assert response.status_code == 401
        assert "error" in response.get_json()
        assert (
            "Authorization required, Request does not contain a token"
            in response.get_json()["error"]
        )
