from flask import Blueprint
from flask_restful import Api
from app.resources.user import AdminUserResource

# Create admin blueprint with API wrapper
admin_bp = Blueprint("admin", __name__)
admin_api = Api(admin_bp)

# Register admin resources with restful routes
admin_api.add_resource(AdminUserResource, "/create", endpoint="create-admin")
