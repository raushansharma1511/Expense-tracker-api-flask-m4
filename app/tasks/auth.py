from flask import current_app
from app.utils.logger import logger
from app.celery_app import celery
from app.utils.email_helper import send_templated_email


@celery.task(name="send_verification_email", bind=True, max_retries=3)
def send_verification_email(self, email, verification_url):
    """
    Task to send a verification email asynchronously.
    Args:
        email (str): Recipient's email address
        verification_url (str): Complete verification URL
    """
    try:
        # Using templated email
        expiry_minutes = int(
            current_app.config["ACCCOUNT_VERIFICATION_LINK_VALIDITY"] / 60
        )
        send_templated_email(
            recipient=email,
            subject="Verify Your Email - Expense Tracker",
            template="emails/auth/verification.html",
            verification_url=verification_url,
            expiry_minutes=expiry_minutes,
        )

        logger.info(f"Verification email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send verification email to {email}: {str(e)}", exc_info=True
        )

        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=e, countdown=retry_in)


@celery.task(name="send_password_reset_email", bind=True, max_retries=3)
def send_password_reset_email(self, email, reset_url):
    """
    Task to send a password reset email asynchronously.
    Args:
        email (str): Recipient's email address
        reset_url (str): Complete password reset URL
    """
    try:
        # Using templated email
        expiry_minutes = int(current_app.config["PASSWORD_RESET_LINK_VALIDITY"] / 60)
        send_templated_email(
            recipient=email,
            subject="Password Reset - Expense Tracker",
            template="emails/auth/password_reset.html",
            reset_url=reset_url,
            expiry_minutes=expiry_minutes,
        )

        logger.info(f"Password reset email sent successfully to {email}")
        return True

    except Exception as e:
        logger.error(
            f"Failed to send password reset email to {email}: {str(e)}", exc_info=True
        )

        # Retry with exponential backoff
        retry_in = 60 * (2**self.request.retries)  # 60s, 120s, 240s
        raise self.retry(exc=e, countdown=retry_in)
