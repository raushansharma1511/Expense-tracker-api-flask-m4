from flask import Blueprint
from flask_restful import Api
from app.resources.report import (
    TransactionReportResource,
    SpendingTrendsResource,
    TransactionExportResource,
)

report_bp = Blueprint("report", __name__)
report_api = Api(report_bp)

# Register endpoints
report_api.add_resource(
    TransactionReportResource,
    "/transactions/summary-report",
    endpoint="transaction-report",
)
report_api.add_resource(
    SpendingTrendsResource,
    "/transactions/spending-trends",
    endpoint="transaction-trends",
)

report_api.add_resource(
    TransactionExportResource,
    "/transactions/history/export",
    endpoint="transaction-export",
)
