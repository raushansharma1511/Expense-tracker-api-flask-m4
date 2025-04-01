from app.urls.auth import auth_bp
from app.urls.user import user_bp
from app.urls.admin import admin_bp
from app.urls.category import category_bp
from app.urls.transaction import transaction_bp
from app.urls.report import report_bp
from app.urls.wallet import wallet_bp
from app.urls.interwallet_transaction import interwallet_transaction_bp
from app.urls.budget import budget_bp
from app.urls.recurring_transaction import recurring_transaction_bp
from app.resources.health_check import health_bp


def register_blueprints(app):
    """Registers all Flask Blueprints (URL routing)"""
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(user_bp, url_prefix="/api/users")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(category_bp, url_prefix="/api/categories")
    app.register_blueprint(wallet_bp, url_prefix="/api/wallets")
    app.register_blueprint(
        interwallet_transaction_bp, url_prefix="/api/interwallet-transactions"
    )
    app.register_blueprint(transaction_bp, url_prefix="/api/transactions")
    app.register_blueprint(
        recurring_transaction_bp, url_prefix="/api/recurring-transactions"
    )
    app.register_blueprint(budget_bp, url_prefix="/api/budgets")
    app.register_blueprint(report_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
