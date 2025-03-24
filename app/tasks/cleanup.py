from flask import current_app
from celery import Celery
from datetime import datetime, timedelta, timezone
from app import create_app, db
from app.models.auth import ActiveAccessToken
from app.models.user import User
from app.models.wallet import Wallet
from app.models.transaction import Transaction
from app.models.budget import Budget
from app.models.category import Category
from app.models.recurring_transaction import RecurringTransaction
from app.models.interwallet_transaction import InterWalletTransaction


from app.celery_app import celery
from app.utils.logger import logger


@celery.task(name="hard_delete_soft_deleted_items", bind=True, max_retries=3)
def hard_delete_soft_deleted_items(self):
    """Celery task to hard delete soft-deleted items older than 30 days."""
    try:
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)
        models = [
            User,
            Wallet,
            Category,
            Transaction,
            Budget,
            RecurringTransaction,
            InterWalletTransaction,
        ]

        for model in models:
            soft_deleted_items = model.query.filter(
                model.is_deleted == True, model.updated_at <= cutoff_date
            ).all()

            for item in soft_deleted_items:
                db.session.delete(item)
                logger.info(f"Hard deleted {model.__name__} with ID {item.id}")

            if soft_deleted_items:
                try:
                    db.session.commit()
                    logger.info(
                        f"Committed hard deletion of {len(soft_deleted_items)} {model.__name__} records."
                    )
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error committing {model.__name__}: {str(e)}")
            else:
                logger.info(f"No {model.__name__} records to hard delete.")

        return "Hard deletion task completed."
    except Exception as e:
        logger.error(f"Error deleting softe deleted resources: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        return False


@celery.task(name="cleanup_expired_access_tokens")
def cleanup_expired_tokens():
    """Delete access tokens older than JWT_ACCESS_TOKEN_EXPIRES minutes."""
    expiration_threshold = datetime.now(timezone.utc) - timedelta(
        seconds=current_app.config["JWT_ACCESS_TOKEN_EXPIRES"]
    )
    expired_tokens = ActiveAccessToken.query.filter(
        ActiveAccessToken.created_at < expiration_threshold
    ).all()

    if expired_tokens:
        for token in expired_tokens:
            db.session.delete(token)
        db.session.commit()
        logger.info(f"Deleted {len(expired_tokens)} expired access tokens.")
    else:
        logger.info("No expired access tokens found.")

    return "Expired access token cleanup task completed."
