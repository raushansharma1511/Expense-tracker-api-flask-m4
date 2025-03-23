from flask import Blueprint
from flask_restful import Api
from app.resources.auth import (
    SignupResource,
    VerifyAccountResource,
    LoginResource,
    RefreshAccessTokenResource,
    LogoutResource,
    PasswordResetRequestResource,
    PasswordResetConfirmResource,
)


auth_bp = Blueprint("auth", __name__)
auth_api = Api(auth_bp)


auth_api.add_resource(SignupResource, "/sign-up", endpoint="sign-up")
auth_api.add_resource(
    VerifyAccountResource, "/verify-user/<token>", endpoint="verify-user"
)
auth_api.add_resource(LoginResource, "/login", endpoint="login")
auth_api.add_resource(LogoutResource, "/logout", endpoint="logout")
auth_api.add_resource(
    RefreshAccessTokenResource, "/refresh-token", endpoint="refresh-token"
)
auth_api.add_resource(
    PasswordResetRequestResource, "/reset-password", endpoint="reset-password"
)
auth_api.add_resource(
    PasswordResetConfirmResource,
    "/reset-password-confirm/<token>",
    endpoint="reset-password-confirm",
)
