from flask import url_for


class TestBudgetDetailResource:
    def test_delete_own_budget(self, client, user_budget, auth_headers, db_session):
        response = client.delete(
            url_for("budget.budget-detail", id=user_budget.id), headers=auth_headers
        )
        assert response.status_code == 204
        assert response.data == b""
        db_session.refresh(user_budget)
        assert user_budget.is_deleted is True

    def test_delete_child_budget_by_parent(self, client, child_budget, auth_headers):
        response = client.delete(
            url_for("budget.budget-detail", id=child_budget.id), headers=auth_headers
        )
        assert response.status_code == 403
        assert "error" in response.get_json()
        assert (
            "You don't have permission to modify your child resource"
            in response.get_json()["error"]
        )

    def test_delete_other_user_budget(
        self, client, test_user2, user_budget, auth_headers_user2
    ):
        response = client.delete(
            url_for("budget.budget-detail", id=user_budget.id),
            headers=auth_headers_user2,
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "Budget not found" in response.get_json()["error"]

    def test_delete_budget_as_admin(
        self, client, child_budget, admin_headers, db_session
    ):
        response = client.delete(
            url_for("budget.budget-detail", id=child_budget.id), headers=admin_headers
        )
        assert response.status_code == 204
        assert response.data == b""
        db_session.refresh(child_budget)
        assert child_budget.is_deleted is True

    def test_delete_already_deleted_budget(
        self, client, user_budget, auth_headers, db_session
    ):
        user_budget.is_deleted = True
        db_session.commit()
        response = client.delete(
            url_for("budget.budget-detail", id=user_budget.id), headers=auth_headers
        )
        assert response.status_code == 404
        assert "error" in response.get_json()
        assert "Budget not found" in response.get_json()["error"]
