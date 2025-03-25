from flask import url_for


class TestBudgetListResource:
    def test_list_budgets_as_user(self, client, user_budget, auth_headers):
        response = client.get(url_for("budget.budgets"), headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(user_budget.id)
        assert data["data"][0]["amount"] == "100.00"
        assert data["data"][0]["spent_amount"] == "0.00"

    def test_list_budgets_as_admin(
        self, client, user_budget, child_budget, admin_headers
    ):
        response = client.get(url_for("budget.budgets"), headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 2

    def test_list_budgets_as_parent(self, client, child_budget, auth_headers):
        response = client.get(
            url_for("budget.budgets") + f"?child_id={child_budget.user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(child_budget.id)

    def test_list_budgets_with_filters(self, client, user_budget, auth_headers):
        query = f"?month={user_budget.month}&year={user_budget.year}"
        response = client.get(url_for("budget.budgets") + query, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1

    def test_list_budgets_invalid_month(self, client, auth_headers):
        response = client.get(
            url_for("budget.budgets") + "?month=11", headers=auth_headers
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "Filtering by month requires specifying a year as well."
            in response.get_json()["error"]
        )

    def test_list_budgets_missing_year_with_month(self, client, auth_headers):
        response = client.get(
            url_for("budget.budgets") + "?month=1", headers=auth_headers
        )
        assert response.status_code == 400
        assert "error" in response.get_json()
        assert (
            "Filtering by month requires specifying a year"
            in response.get_json()["error"]
        )
