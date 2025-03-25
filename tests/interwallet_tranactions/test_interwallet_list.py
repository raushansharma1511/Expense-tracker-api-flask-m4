from flask import url_for


class TestInterWalletTransactionListCreateResource:
    def test_list_transactions_as_user(
        self, client, user_interwallet_transaction, auth_headers
    ):
        response = client.get(
            url_for("interwallet_transaction.transactions"), headers=auth_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(user_interwallet_transaction.id)
        assert data["data"][0]["amount"] == "50.00"

    def test_list_transactions_as_admin(
        self,
        client,
        user_interwallet_transaction,
        child_interwallet_transaction,
        admin_headers,
    ):
        response = client.get(
            url_for("interwallet_transaction.transactions"), headers=admin_headers
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 2

    def test_list_child_transactions_as_parent(
        self, client, child_interwallet_transaction, auth_headers
    ):
        response = client.get(
            url_for("interwallet_transaction.transactions")
            + f"?child_id={child_interwallet_transaction.user_id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == str(child_interwallet_transaction.id)

    def test_list_transactions_with_date_filter(
        self, client, user_interwallet_transaction, auth_headers
    ):
        date = user_interwallet_transaction.transaction_at.strftime("%Y-%m-%d")
        response = client.get(
            url_for("interwallet_transaction.transactions") + f"?from_date={date}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "data" in data
        assert len(data["data"]) == 1

    def test_list_transactions_invalid_date(self, client, auth_headers):
        response = client.get(
            url_for("interwallet_transaction.transactions") + "?from_date=invalid",
            headers=auth_headers,
        )
        assert response.status_code == 200  # Invalid dates are logged but don’t fail
        data = response.get_json()
        assert "data" in data
