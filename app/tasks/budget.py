from flask import current_app
from app.extensions import db
from app.utils.logger import logger
from app.celery_app import celery
from app.models.budget import Budget
from app.models.user import User
from app.models.category import Category
from app.utils.email_helper import send_templated_email
from decimal import Decimal
import calendar
from app.utils.constants import BUDGET_WARNING_THRESHOLD, BUDGET_EXCEEDED_THRESHOLD


@celery.task(name="check_budget_thresholds", bind=True, max_retries=3)
def check_budget_thresholds(self, budget_id):
    """
    Check budget thresholds and manage notification flags comprehensively.
    """
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            logger.warning(f"Budget not found for threshold check: {budget_id}")
            return False

        percentage_used = budget.percentage_used
        notification_sent = False

        if percentage_used < BUDGET_WARNING_THRESHOLD:
            if budget.warning_notification_sent or budget.exceeded_notification_sent:
                budget.warning_notification_sent = False
                budget.exceeded_notification_sent = False

        elif BUDGET_WARNING_THRESHOLD <= percentage_used < BUDGET_EXCEEDED_THRESHOLD:
            if budget.exceeded_notification_sent:
                budget.exceeded_notification_sent = False

            if not budget.warning_notification_sent:
                send_budget_notification.delay(budget.id, "warning", percentage_used)
                budget.warning_notification_sent = True
                notification_sent = True

        else:
            if not budget.exceeded_notification_sent:
                send_budget_notification.delay(budget.id, "exceeded", percentage_used)
                budget.exceeded_notification_sent = True
                notification_sent = True

        db.session.commit()

        return notification_sent

    except Exception as e:
        logger.error(f"Error checking budget thresholds: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        return False


@celery.task(name="send_budget_notification", bind=True, max_retries=3)
def send_budget_notification(self, budget_id, notification_type, percentage=None):
    """
    Send a budget notification (warning or exceeded).

    Args:
        budget_id: ID of the budget.
        notification_type: Either "warning" or "exceeded".
        percentage: Optional specific percentage to mention.
    """
    try:
        budget = Budget.query.get(budget_id)
        if not budget:
            logger.warning(
                f"Budget not found for {notification_type} notification: {budget_id}"
            )
            return False

        user = User.query.get(budget.user_id)
        if not user or not user.email:
            logger.warning(f"User not found or no email for budget {budget_id}")
            return False

        category = Category.query.get(budget.category_id)
        if not category:
            logger.warning(f"Category not found for budget {budget_id}")
            return False

        # Get month name dynamically
        month_name = calendar.month_name[budget.month]

        # Default to actual percentage if not provided
        percentage = percentage or budget.percentage_used

        email_data = {
            "recipient": user.email,
            "category_name": category.name,
            "month_name": month_name,
            "year": budget.year,
            "budget_amount": float(budget.amount),
            "spent_amount": float(budget.spent_amount),
        }

        # Customize email subject & template based on notification type
        if notification_type == "warning":
            email_data.update(
                {
                    "subject": f"Budget Warning: {category.name} budget is at {percentage}%",
                    "template": "emails/budget/warning.html",
                    "remaining": float(budget.remaining),
                    "percentage": percentage,
                }
            )
        elif notification_type == "exceeded":
            email_data.update(
                {
                    "subject": f"Budget Alert: {category.name} budget has been exceeded!",
                    "template": "emails/budget/exceeded.html",
                    "overspent": float(
                        max(Decimal("0"), budget.spent_amount - budget.amount)
                    ),
                }
            )
        else:
            logger.error(f"Invalid notification type: {notification_type}")
            return False

        # Send templated email
        send_templated_email(**email_data)

        logger.info(
            f"Sent budget {notification_type} notification to {user.email} for budget {budget_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Error sending budget {notification_type} notification: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        return False
