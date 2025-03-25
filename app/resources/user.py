from flask_restful import Resource
from flask import request, g
from flask import url_for
from marshmallow import ValidationError
from app.extensions import db
from app.models.user import User
from app.schemas.auth import user_schema
from app.schemas.user import (
    user_profile_schema,
    users_profile_schema,
    user_update_schema,
    email_change_request_schema,
    email_change_confirm_schema,
    user_deletion_schema,
    password_update_schema,
)
from app.services.user import (
    request_email_change,
    confirm_email_change,
    delete_user_account,
    generate_admin_email_change_token,
    verify_admin_email_change_token,
    logout_other_sessions,
)
from app.services.auth import prepare_user_creation
from app.utils.permissions import (
    authenticated_user,
    admin_required,
    object_permission,
    user_profile_permission,
    user_self_permission,
    child_user_permission,
)
from app.tasks.user import send_admin_email_change_verification
from app.utils.responses import validation_error_response
from app.utils.pagination import paginate
from app.utils.logger import logger
from app.utils.enums import UserRole


class UserListResource(Resource):
    """Resource to list all users (admin only)"""

    @authenticated_user
    @admin_required
    def get(self):
        """Get paginated list of all users"""
        logger.info(f"admin user {g.user} requested list of all users")

        query = User.query.filter_by(is_deleted=False).order_by(User.created_at.desc())

        logger.info(f"Returned list of all users to admin user {g.user}")
        result = paginate(
            query=query, schema=users_profile_schema, endpoint="user.users"
        )
        return result, 200


class UserDetailResource(Resource):
    """Resource for getting, updating and deleting user profiles"""

    method_decorators = [
        object_permission(User, check_fn=user_profile_permission),
        authenticated_user,
    ]

    def get(self, id):
        """Get user details"""
        logger.info(
            f"User {g.user} requested to get the profile details of user {g.object}"
        )

        user = g.object
        logger.info(f"Returned profile details for user {g.user}")
        return user_profile_schema.dump(user), 200

    def patch(self, id):
        """Update user profile (username, name)"""
        try:
            # Get data and users
            data = request.get_json() or {}

            logger.info(
                f"User {g.user} requested to update the profile details of user {g.object} with data {data}"
            )
            user = g.object
            updated_user = user_update_schema.load(data, instance=user, partial=True)
            db.session.commit()

            logger.info(f"Profile details updated successfully for user {g.user}")
            return user_profile_schema.dump(updated_user), 200

        except ValidationError as e:
            return validation_error_response(e)

    def delete(self, id):
        """Soft delete user"""
        try:
            # Get request data and users
            data = request.get_json() or {}
            logger.info(f"User {g.user} requested to delete user {g.object}")

            current_user = g.user
            target_user = g.object
            current_user_role = g.role

            user_deletion_schema.context = {
                "current_user": current_user,
                "target_user": target_user,
                "current_user_role": current_user_role,
            }
            validated_data = user_deletion_schema.load(data)
            # Delete the user account
            delete_user_account(current_user, target_user)

            return "", 204
        except ValidationError as e:
            return validation_error_response(e)


class PasswordUpdateResource(Resource):
    """Resource for updating a user's password with user_id in URL
    - Only the user themselves can update their password
    """

    method_decorators = [authenticated_user]

    def post(self, id):
        try:
            # Get request data
            data = request.get_json() or {}
            target_user = User.query.filter(
                User.id == id, User.is_deleted == False
            ).first()
            if not target_user:
                return {"error": "User not found"}, 404

            if target_user != g.user:
                return {"error": "User can only update their own password"}, 403

            logger.info(f"User {g.user} requested to update his account password")

            password_update_schema.context = {"target_user": target_user}
            validated_data = password_update_schema.load(data)

            # Update password
            target_user.set_password(validated_data["new_password"])
            db.session.commit()
            logout_other_sessions(target_user)

            logger.info(f"Password updated successfully for user: {target_user.email}")

            return {"message": "Password updated successfully"}, 200

        except ValidationError as err:
            logger.warning(f"Validation error: {err.messages}")
            return validation_error_response(err)


class UserEmailChangeResource(Resource):
    """Resource for email change requests with different workflows based on user type.
    1. Regular user or child user changing own email or admin user changing own email -> OTP verification flow
    2. Admin user changing another user's email -> Token verification flow
    """

    method_decorators = [
        object_permission(User, check_fn=user_profile_permission),
        authenticated_user,
    ]

    def post(self, id):
        try:
            data = request.get_json() or {}
            request_user = g.user
            target_user = g.object  # Already set by object_permission decorator
            logger.info(
                f"User {request_user.id} requesting email change for user {target_user.id} to {data.get('new_email', 'unknown')}"
            )
            # Validate request data
            email_change_request_schema.context = {"user": target_user}
            validated_data = email_change_request_schema.load(data)
            new_email = validated_data["new_email"]

            # User changing their own email (admin or regular) otp flow
            if str(request_user.id) == str(id):
                request_email_change(target_user, new_email)
                return {
                    "message": "Enter the otps sent to your current and new email addresses"
                }, 200

            # Admin user changing another user's email
            token = generate_admin_email_change_token(target_user, new_email)
            verification_url = url_for("user.verify-email", token=token, _external=True)

            # Send verification email to the new email address
            send_admin_email_change_verification.delay(
                new_email, verification_url, target_user.username
            )
            logger.info(
                f"Verification email sent to {new_email} for admin-initiated email change for user {target_user.id}"
            )
            return {
                "message": f"Verification link sent to {new_email}. User must click the link to confirm email change."
            }, 200

        except ValidationError as e:
            return validation_error_response(e)


class EmailChangeConfirmResource(Resource):
    """Resource for confirming email changes with separate OTPs"""

    method_decorators = [
        object_permission(User, check_fn=user_self_permission),
        authenticated_user,
    ]

    def post(self, id):
        """
        Confirm email change with separate OTPs for each email.
        Using user_password_permission to ensure only the user themselves can confirm.
        """
        try:
            data = request.get_json() or {}
            target_user = g.object  # Set by the object_permission decorator

            # Validate OTPs
            validated_data = email_change_confirm_schema.load(data)

            # Confirm email change with both OTPs
            confirm_email_change(
                target_user,
                validated_data["current_email_otp"],
                validated_data["new_email_otp"],
            )
            logger.info(f"Email updated successfully for user {target_user}")
            return {"message": "Email address updated successfully"}, 200

        except ValidationError as e:
            return validation_error_response(e)


class EmailChangeVerifyTokenResource(Resource):
    """Resource for verifying email change token (admin-initiated flow)"""

    def get(self, token):
        """Verify email change token and update user email"""
        try:
            # Verify token and update email
            if not token:
                return {"error": "Token is missing"}, 400

            user_id, new_email = verify_admin_email_change_token(token)

            if not user_id or not new_email:
                return {"error": "Invalid or expired verification token"}, 400

            # Get the user
            user = db.session.get(User, user_id)
            if not user or user.is_deleted:
                return {"error": "User not found"}, 404

            # Update the user's email
            user.email = new_email
            db.session.commit()

            logger.info(f"Email updated successfully for user {user} to {new_email}")
            return {"message": "Email address updated successfully"}, 200

        except Exception as e:
            logger.error(f"Error verifying email change token: {str(e)}", exc_info=True)
            return {"error": "Failed to verify email change", "details": str(e)}, 500


class ChildUserResource(Resource):
    "Resource for the creation and list the child user for a particular user"

    method_decorators = [child_user_permission()]

    def post(self, id):
        try:
            parent_user: User = g.object

            if parent_user.has_child():
                logger.error(f"User {parent_user.id} already has a child user")
                return {"error": "A child user already exists for this user"}, 400

            data = request.get_json()

            child_user_data = user_schema.load(data)
            child_user_data.role = UserRole.CHILD_USER

            token = prepare_user_creation(child_user_data, parent_user)

            return {
                "message": f"Child user registration initiated. Please check your email to verify the account.",
            }, 200

        except ValidationError as err:
            return validation_error_response(err)

    def get(self, id):
        """Get child users for a parent"""

        parent_user = g.object

        child = parent_user.get_child()

        if not child:
            return {"message": "No child user found for this account"}, 404

        result = user_profile_schema.dump(child)

        return result, 200


class AdminUserResource(Resource):
    """Resource for admin user creation - only accessible by existing admins"""

    method_decorators = [admin_required, authenticated_user]

    def post(self):
        """
        Create a new admin user
        Only existing admins can create other admin users
        """
        try:
            admin_user = g.user
            logger.info(f"Admin {admin_user.id} is creating a new admin user")

            data = request.get_json() or {}

            new_admin_data = user_schema.load(data)
            new_admin_data.role = UserRole.ADMIN

            token = prepare_user_creation(new_admin_data)

            logger.info(f"Admin user creation initiated by admin {admin_user.id}")

            return {
                "message": f"Admin user registration initiated. Please check the email to verify the account.",
                "token": token,
            }, 200

        except ValidationError as err:
            logger.warning(
                f"Validation error during admin user creation: {err.messages}"
            )
            return validation_error_response(err)
