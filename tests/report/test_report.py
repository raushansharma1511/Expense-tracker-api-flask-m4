from datetime import datetime, timedelta
from flask import url_for
from unittest.mock import patch


class TestReport:
    def test_transaction_report_success(
        self, client, auth_headers, test_user, user_transaction, db_session
    ):
        """Test successful transaction report generation for a normal user"""
        start_date = datetime.today().date() - timedelta(days=30)
        end_date = datetime.today().date() + timedelta(days=30)

        url = url_for(
            "report.transaction-report", start_date=start_date, end_date=end_date
        )

        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        assert data["start_date"] == start_date.strftime("%Y-%m-%d")
        assert data["end_date"] == end_date.strftime("%Y-%m-%d")
        assert float(data["total_debit"]) == 50.00

    def test_spending_trends_success(
        self, client, auth_headers, test_user, user_transaction, app
    ):
        """Test successful spending trends generation"""
        start_date = datetime.today().date() - timedelta(days=30)
        end_date = datetime.today().date() + timedelta(days=30)
        url = url_for(
            "report.transaction-trends", start_date=start_date, end_date=end_date
        )
        response = client.get(url, headers=auth_headers)
        assert response.status_code == 200
        data = response.get_json()
        print(data)
        assert len(data["spending_trends"]) == 1
        assert data["spending_trends"][0]["category"]["name"] == "Test category"
        assert float(data["spending_trends"][0]["amount"]) == 50.00
        assert float(data["total_debit"]) == 50.00

    @patch("app.services.export_report.generate_and_send_export.delay")
    def test_transaction_export_success(
        self,
        generate_report_mock,
        client,
        auth_headers,
        test_user,
        user_transaction,
        user_interwallet_transaction,
    ):
        """Test successful transaction export request for normal user"""
        start_date = datetime.today().date() - timedelta(days=30)
        end_date = datetime.today().date() + timedelta(days=30)
        url = url_for(
            "report.transaction-export",
            start_date=start_date,
            end_date=end_date,
            format="pdf",
        )

        generate_report_mock.return_value = None

        response = client.get(url, headers=auth_headers)

        assert response.status_code == 202
        data = response.get_json()
        assert (
            "Transaction history export request received".lower()
            in data["message"].lower()
        )
        generate_report_mock.assert_called_once()
