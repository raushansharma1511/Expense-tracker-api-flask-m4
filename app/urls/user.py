from flask import Blueprint
from flask_restful import Api
from app.resources.user import (
    UserListResource,
    UserDetailResource,
    UserEmailChangeResource,
    EmailChangeConfirmResource,
    PasswordUpdateResource,
    EmailChangeVerifyTokenResource,
    ChildUserResource,
)

# Create user blueprint with API wrapper
user_bp = Blueprint("user", __name__)
user_api = Api(user_bp)

# Register user resources with restful routes
user_api.add_resource(UserListResource, "", endpoint="users")

user_api.add_resource(UserDetailResource, "/<id>", endpoint="user-detail")
user_api.add_resource(
    PasswordUpdateResource, "/<id>/update-password", endpoint="update-password"
)

user_api.add_resource(
    UserEmailChangeResource, "/<id>/update-email", endpoint="update-email"
)
user_api.add_resource(
    EmailChangeConfirmResource,
    "/<id>/update-email/confirm",
    endpoint="update-email-confirm",
)
user_api.add_resource(
    EmailChangeVerifyTokenResource, "/api/verify-email/<token>", endpoint="verify-email"
)

user_api.add_resource(ChildUserResource, "/<id>/child", endpoint="child-user")
