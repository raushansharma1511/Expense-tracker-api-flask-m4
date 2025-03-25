from marshmallow import ValidationError


from app.services.report import parse_and_validate_dates
from app.utils.enums import UserRole
from app.models.transaction import Transaction
from app.models.interwallet_transaction import InterWalletTransaction
from app.tasks.report import generate_and_send_export
from app.models.user import User
from app.utils.validators import is_valid_uuid
from app.utils.logger import logger


def export_transactions(current_user, query_params=None):
    """
    Export transactions to PDF or CSV and email to user.

    Args:
        current_user: The authenticated user
        query_params: Query parameters including start_date, end_date, format, user_id, and child_id

    Returns:
        dict: Status of export request
    """
    # Initialize query params
    query_params = query_params or {}

    start_date, end_date = parse_and_validate_dates(
        query_params.get("start_date"), query_params.get("end_date")
    )

    export_format = query_params.get("format", "pdf").lower()
    if export_format not in ["pdf", "csv"]:
        raise ValidationError("Invalid export format. Must be 'pdf' or 'csv'")

    if current_user.role == UserRole.ADMIN:
        if "user_id" in query_params and query_params["user_id"]:
            user_id = query_params["user_id"]

            if is_valid_uuid(user_id):
                target_user = User.query.filter_by(id=user_id, is_deleted=False).first()
                if not target_user:
                    raise ValidationError(f"User with ID {user_id} not found")
            else:
                raise ValidationError(f"Invalid user_id format: {user_id}")
        else:
            raise ValidationError("Admin users must provide a user_id of a normal user")

    elif current_user.role == UserRole.USER:
        if "child_id" in query_params and query_params["child_id"]:
            child_id = query_params["child_id"]

            if is_valid_uuid(child_id):
                # Verify this is actually the child of the user
                child = current_user.get_child()
                is_child = child and str(child.id) == child_id

                if not is_child:
                    raise ValidationError(f"You are not the parent of user {child_id}")

                target_user = child
            else:
                raise ValidationError(f"Invalid child_id format: {child_id}")
        else:
            target_user = current_user

    else:
        target_user = current_user

    is_transaction_exists = (
        target_user.transactions.filter(
            Transaction.transaction_at.between(start_date, end_date),
            Transaction.is_deleted.is_(False),
        ).first()
        is not None
        or target_user.interwallet_transactions.filter(
            InterWalletTransaction.transaction_at.between(start_date, end_date),
            InterWalletTransaction.is_deleted.is_(False),
        ).first()
        is not None
    )
    if not is_transaction_exists:
        raise ValidationError("No transactions found for the specified date range")

    # Schedule task to generate and send export
    generate_and_send_export.delay(
        current_user_id=str(current_user.id),
        target_user_email=target_user.email,
        query_params=query_params,
        export_format=export_format,
    )

    # Return immediate success response
    return {
        "message": f"Transaction history export request received. The {export_format.upper()} will be sent to {target_user.email} shortly."
    }, 202
