from app.utils.logger import logger
from app.utils.validators import is_valid_uuid
from app.models.user import User
from marshmallow import ValidationError
from app.utils.enums import UserRole


def fetch_standard_resources(
    model_class,
    user,
    role,
    query_params={},
    user_field="user_id",
):
    """
    Generic method to fetch standard resources according to user role and permissions.

    Args:
        model_class: The SQLAlchemy model class to query
        user: The authenticated user requesting resources
        role: Role of the requesting user
        query_params: Dict containing optional filters:
            - user_id: For ADMIN to filter by specific user
            - child_id: For USER to filter by their child
        user_field: Name of the field in the model that references the user (default: 'user_id')

    Returns:
        SQLAlchemy query object with basic role-based filtering applied

    Raises:
        ValidationError: For invalid user_id or child_id
    """
    resource_name = model_class.__name__
    logger.info(f"Fetching {model_class.__name__}s for user {user.id} with role {role}")

    # Start with base query
    query = model_class.query

    # Apply role-based filtering
    if role == UserRole.ADMIN.value:

        if "user_id" in query_params and query_params["user_id"]:
            user_id = query_params["user_id"]

            if is_valid_uuid(user_id):
                target_user = User.query.filter_by(id=user_id, is_deleted=False).first()
                if not target_user:
                    logger.warning(
                        f"Admin {user.id} requested non-existent user {user_id}"
                    )
                    raise ValidationError(f"User with ID {user_id} not found")

                # Filter by specified user
                query = query.filter(getattr(model_class, user_field) == user_id)
                logger.info(f"Admin filtering {resource_name}s for user: {user_id}")
            else:
                logger.warning(f"Invalid user_id format in request: {user_id}")
                raise ValidationError(f"Invalid user_id format: {user_id}")

    elif role == UserRole.USER.value:
        # USER ROLE - Can only see non-deleted resources
        query = query.filter(model_class.is_deleted == False)

        # Check if filtering by child
        if "child_id" in query_params and query_params["child_id"]:
            child_id = query_params["child_id"]

            if is_valid_uuid(child_id):
                # Verify this is actually the child of the user
                child = user.get_child()
                is_child = child and str(child.id) == child_id

                if is_child:
                    query = query.filter(getattr(model_class, user_field) == child_id)
                    logger.info(
                        f"User {user.id} filtering {resource_name}s for their child {child_id}"
                    )
                else:
                    logger.warning(
                        f"User {user.id} attempted to access {resource_name}s of non-child user {child_id}"
                    )
                    raise ValidationError(f"You are not the parent of user {child_id}")
            else:
                logger.warning(f"Invalid child_id format in request: {child_id}")
                raise ValidationError(f"Invalid child_id format: {child_id}")
        else:
            # Filter to user's own resources
            query = query.filter(getattr(model_class, user_field) == user.id)
            logger.info(f"User {user.id} retrieving own {resource_name}s")

    else:  # CHILD_USER
        query = query.filter(
            model_class.is_deleted == False, getattr(model_class, user_field) == user.id
        )
        logger.info(f"Child user {user.id} retrieving own {resource_name}s")

    return query
