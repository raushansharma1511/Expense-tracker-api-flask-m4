from flask import url_for
from app.models.transaction import Transaction, TransactionType


class TestTransactionList:
    """Tests for transaction listing and creation"""

    def test_list_transactions_as_admin(
        self, client, admin_headers, user_transaction, child_transaction
    ):
        """Test admin lists all transactions"""
        url = url_for("transaction.transactions")
        response = client.get(url, headers=admin_headers)
        assert response.status_code == 200
        data = response.get_json()
        transactions = data["data"]
        assert len(transactions) >= 2
        assert any(t["id"] == str(user_transaction.id) for t in transactions)
        assert any(t["id"] == str(child_transaction.id) for t in transactions)

    def test_list_own_transactions_as_user(
        self, client, auth_headers, user_transaction, child_transaction
    ):
        """Test user lists own transactions only"""
        url = url_for("transaction.transactions")
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        transactions = data["data"]
        assert any(t["id"] == str(user_transaction.id) for t in transactions)
        assert not any(t["id"] == str(child_transaction.id) for t in transactions)

    def test_list_child_transactions_by_parent(
        self, client, auth_headers, child_user, child_transaction
    ):
        """Test parent lists child’s transactions"""
        url = url_for("transaction.transactions", child_id=str(child_user.id))
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        transactions = data["data"]
        assert any(t["id"] == str(child_transaction.id) for t in transactions)

    def test_list_transactions_as_child(
        self, client, child_headers, user_transaction, child_transaction
    ):
        """Test child lists own transactions only"""
        url = url_for("transaction.transactions")
        response = client.get(url, headers=child_headers)
        assert response.status_code == 200
        data = response.get_json()
        transactions = data["data"]
        assert any(t["id"] == str(child_transaction.id) for t in transactions)
        assert not any(t["id"] == str(user_transaction.id) for t in transactions)

    def test_list_transactions_unauthenticated(self, client):
        """Test listing without auth"""
        url = url_for("transaction.transactions")
        response = client.get(url)
        assert response.status_code == 401

    def test_list_with_type_filter(
        self, client, auth_headers, user_transaction, user_income_transaction
    ):
        """Test filtering by transaction type"""
        url = url_for("transaction.transactions", type="CREDIT")
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        transactions = data["data"]
        assert all(t["type"] == "CREDIT" for t in transactions)

    def test_list_with_invalid_type_filter(self, client, auth_headers):
        """Test filtering with invalid type"""
        url = url_for("transaction.transactions", type="INVALID")
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid transaction type" in data["error"]

    def test_list_with_date_filter(
        self, client, auth_headers, user_transaction, db_session
    ):
        """Test filtering by date range"""
        date_str = user_transaction.transaction_at.strftime("%Y-%m-%d")
        url = url_for("transaction.transactions", from_date=date_str, to_date=date_str)
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) >= 1

    def test_list_with_invalid_date_filter(self, client, auth_headers):
        """Test filtering with invalid date"""
        url = url_for("transaction.transactions", from_date="invalid-date")
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid from_date" in data["error"]

    def test_list_pagination(
        self, client, auth_headers, test_user, user_wallet, user_category, db_session
    ):
        """Test pagination"""
        for i in range(3):
            t = Transaction(
                user_id=test_user.id,
                wallet_id=user_wallet.id,
                category_id=user_category.id,
                amount=10.00,
                type=TransactionType.DEBIT,
                description=f"Test {i}",
            )
            db_session.add(t)
        db_session.commit()
        url = url_for("transaction.transactions", per_page=2, page=1)
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert len(data["data"]) == 2
        assert data["total_items"] >= 3
