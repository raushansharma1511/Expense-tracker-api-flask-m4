from flask_restful import Resource
from flask import g, request
from marshmallow import ValidationError

from app.services.report import generate_transaction_report, get_spending_trends
from app.utils.permissions import authenticated_user
from app.utils.logger import logger
from app.services.export_report import export_transactions
from app.utils.responses import validation_error_response


class TransactionReportResource(Resource):
    """Resource for generating transaction reports"""

    @authenticated_user
    def get(self):
        """Generate a transaction report with date range filtering"""
        try:
            user = g.user
            # Get query parameters for filtering
            query_params = request.args.to_dict()

            logger.info(
                f"User {user.id} requested transaction report with params: {query_params}"
            )
            report_data = generate_transaction_report(user, query_params)

            logger.info(f"Transaction summary report generated successfully")
            return report_data, 200

        except ValidationError as err:
            logger.warning(f"Validation error in report generation: {str(err)}")
            return {"error": str(err)}, 400


class SpendingTrendsResource(Resource):
    """Resource for generating spending trends"""

    @authenticated_user
    def get(self):
        """Generate spending trends by category with date range filtering"""
        try:
            user = g.user
            # Get query parameters for filtering
            query_params = request.args.to_dict()
            logger.info(
                f"User {user.id} requested spending trends with params: {query_params}"
            )

            trends_data = get_spending_trends(user, query_params)
            logger.info(f"Spending trends generated successfully")
            return trends_data, 200

        except ValidationError as err:
            return {"error": str(err)}, 400


class TransactionExportResource(Resource):
    """Resource for exporting transactions"""

    @authenticated_user
    def get(self):
        """Export transactions in PDF or CSV format"""
        try:
            user = g.user
            query_params = request.args.to_dict()

            logger.info(
                f"User {user.id} requested transaction export with params: {query_params}"
            )

            logger.info(f"Transaction export generated successfully")
            return export_transactions(user, query_params)

        except ValidationError as err:
            logger.warning(f"Validation error in export request: {str(err)}")
            return validation_error_response(err)
