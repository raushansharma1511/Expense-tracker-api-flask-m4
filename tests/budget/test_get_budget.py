from flask import url_for


class TestBudgetDetailResource:
    def test_get_own_budget(self, client, user_budget, auth_headers):
        response = client.get(
            url_for("budget.budget-detail", id=user_budget.id), headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert data["id"] == str(user_budget.id)
        assert data["amount"] == "100.00"

    def test_get_child_budget_by_parent(self, client, child_budget, auth_headers):
        response = client.get(
            url_for("budget.budget-detail", id=child_budget.id), headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert data["id"] == str(child_budget.id)

    def test_get_other_user_budget(
        self, client, test_user2, user_budget, auth_headers_user2
    ):
        response = client.get(
            url_for("budget.budget-detail", id=user_budget.id),
            headers=auth_headers_user2,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "Budget not found" in response.get_json()["error"]

    def test_get_budget_as_admin(self, client, child_budget, admin_headers):
        response = client.get(
            url_for("budget.budget-detail", id=child_budget.id), headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "id" in data
        assert data["id"] == str(child_budget.id)

    def test_get_deleted_budget(self, client, user_budget, auth_headers, db_session):
        user_budget.is_deleted = True
        db_session.commit()
        response = client.get(
            url_for("budget.budget-detail", id=user_budget.id), headers=auth_headers
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "Budget not found" in response.get_json()["error"]
