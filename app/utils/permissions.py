from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from flask import jsonify, request, g
from functools import wraps
from app.models.user import User
from app.models.auth import ActiveAccessToken
import uuid
from app.utils.logger import logger
from app.utils.validators import is_valid_uuid
from app.extensions import db
from flask_jwt_extended import get_jwt
from app.utils.enums import UserRole


def get_jwt_role():
    """Get user role from JWT claims"""
    claims = get_jwt()
    return claims.get("role")


def authenticated_user(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        token = request.headers.get("Authorization").split(" ")[1]
        token_entry = ActiveAccessToken.query.filter_by(access_token=token).first()

        if not token_entry or not token_entry.user:
            logger.error(
                f"Authentication failed: Invalid token or no user for '{token}'"
            )
            return {"error": "Invalid authorization detail."}, 401

        # Set user in context
        g.user = token_entry.user

        # Also set role from token for easier access
        g.role = get_jwt_role()

        logger.info(f"User authenticated successfully: {g.user.id}, role: {g.role}")
        return fn(*args, **kwargs)

    return wrapper


def object_permission(model_class, id_param="id", check_fn=None):
    """
    Generic object permission decorator that retrieves an object and checks permissions.
    """

    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):

            object_id = kwargs.get(id_param)
            if not object_id:
                logger.warning(f"Missing {id_param} in request")
                return {"error": "Missing object ID"}, 400

            obj = db.session.get(model_class, uuid.UUID(object_id))
            if not obj:
                logger.error(f"{model_class.__name__} not found for ID: {object_id}")
                return {"error": f"{model_class.__name__} not found."}, 404

            request_user = g.user
            request_method = request.method
            request_user_role = g.role

            if check_fn:
                has_permission = check_fn(request_user, obj, request_method)
                if isinstance(has_permission, tuple):
                    return has_permission
            else:
                has_permission = False
                owner_id = obj.user_id

                if request_method == "GET":

                    if request_user_role == UserRole.ADMIN.value:
                        has_permission = True

                    elif request_user_role == UserRole.CHILD_USER.value:
                        has_permission = (
                            not obj.is_deleted and owner_id == request_user.id
                        )

                    else:
                        if not obj.is_deleted:

                            if owner_id == request_user.id:
                                has_permission = True
                            else:
                                child = request_user.get_child()
                                has_permission = child and owner_id == child.id
                # For POST, PUT, DELETE
                else:
                    if not obj.is_deleted:
                        if request_user_role == UserRole.ADMIN.value:
                            has_permission = True
                        elif request_user_role == UserRole.CHILD_USER.value:
                            has_permission = owner_id == request_user.id
                        else:
                            # Regular user
                            if owner_id == request_user.id:
                                has_permission = True
                            else:
                                # check if the user is a parent of the owner
                                child = request_user.get_child()
                                if child and owner_id == child.id:
                                    return {
                                        "error": "You don't have permission to modify your child resource."
                                    }, 403

            # Check if permission is granted
            if not has_permission:
                logger.error(
                    f"Permission denied for user {request_user.id} on {model_class.__name__} {obj.id}"
                )
                return {"error": f"{model_class.__name__} not found"}, 404

            g.object = obj
            logger.info(
                f"Permission granted for user {request_user.id} on {model_class.__name__} {obj.id} ({request_method})"
            )
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def admin_required(fn):
    """
    Decorator to ensure a user is authenticated and is admin.
    """

    @wraps(fn)
    def wrapper(*args, **kwargs):
        if g.role != UserRole.ADMIN.value:
            logger.error(f"Admin access denied for user {g.user.id}: Not an Admin user")
            return {"error": "You don't have access to this endpoint."}, 403
        logger.info(f"Admin access granted for user {g.user.id}")
        return fn(*args, **kwargs)

    return wrapper


def user_profile_permission(request_user, target_user, request_method):
    """
    Custom permission function for password updates.
    """
    request_user_role = g.role

    if request_method == "GET":
        if request_user_role == UserRole.ADMIN.value:
            return True
        elif (
            request_user_role == UserRole.CHILD_USER.value
            and target_user.id == request_user.id
        ):
            return True
        else:
            if target_user.is_deleted == False:
                if target_user.id == request_user.id:
                    return True
                else:
                    child = request_user.get_child()
                    if child and target_user.id == child.id:
                        return True
            return False
    else:
        if not target_user.is_deleted:
            if request_user_role == UserRole.ADMIN.value:
                return True
            elif target_user.id == request_user.id:
                return True
            else:
                child = request_user.get_child()
                if child and target_user.id == child.id:
                    return {
                        "error": "You don't have permission to modify your child."
                    }, 403
    return False


def user_self_permission(user, target_user, request_method):
    """Permissions for update password"""

    if not target_user.is_deleted and user.id == target_user.id:
        return True
    return {"error": "Unauthorized"}, 403


def category_permission(user, obj, request_method):
    """
    Permission function for categories.
    """
    user_role = g.role

    if request_method == "GET":
        if user_role == UserRole.ADMIN.value:
            return True

        elif user_role == UserRole.CHILD_USER.value:
            return not obj.is_deleted and (obj.is_predefined or obj.user_id == user.id)

        else:
            if obj.is_deleted == False:
                if obj.is_predefined or obj.user_id == user.id:
                    return True
                else:
                    child = user.get_child()
                    if child and obj.user_id == child.id:
                        return True
            return False
    else:
        if not obj.is_deleted:
            if user_role == UserRole.ADMIN.value:
                return True

            elif obj.user_id == user.id:
                return True

            else:
                child = user.get_child()
                if child and obj.user_id == child.id:
                    return {
                        "error": "You don't have permission to modify your child's resource."
                    }, 403
    return False


def child_user_permission(model_class=User, id_param="id"):
    """
    Permission decorator for child user management.

    This checks:
    1. User is authenticated
    2. User is not a child user
    3. Target user exists and is a regular user
    4. If request user is regular user, they can only manage their own child users
    5. For POST requests, ensures target user doesn't already have a child
    """

    def decorator(fn):
        @wraps(fn)
        @authenticated_user
        def wrapper(*args, **kwargs):
            # User is already authenticated by @authenticated_user
            request_user = g.user
            role = g.role

            if role == UserRole.CHILD_USER.value:
                logger.error(
                    f"Child user {request_user.id} cannot have access to this endpoint."
                )
                return {"error": "You don't have access to this endpoint."}, 403

            user_id = kwargs.get(id_param)

            target_user = db.session.get(model_class, uuid.UUID(user_id))

            if not target_user or target_user.is_deleted:
                logger.error(f"User not found for ID: {user_id}")
                return {"error": "User not found"}, 404

            # Target user must be a regular user
            if target_user.role != UserRole.USER:
                logger.error(
                    f"User {target_user.id} is not a regular user and cannot have child users"
                )
                return {"error": "Only regular users can have child users"}, 400

            # Permission check based on role
            if role == UserRole.USER.value:
                # Regular users can only manage their own child users
                if request_user.id != target_user.id:
                    logger.error(
                        f"User {request_user.id} cannot manage child users for {target_user.id}"
                    )
                    return {"error": "You can only manage your own child users"}, 403

            # Set object in context for the view function
            g.object = target_user

            logger.info(
                f"User {request_user.id} granted permission for child user management of {target_user.id}"
            )
            return fn(*args, **kwargs)

        return wrapper

    return decorator
