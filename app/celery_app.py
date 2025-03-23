from celery import Celery
import os
from celery.schedules import crontab


def make_celery(app=None):
    """
    Create a Celery instance that integrates with Flask application context.
    """
    celery = Celery(
        "app",
        broker=os.getenv("CELERY_BROKER_URL"),
        backend=os.getenv("CELERY_RESULT_BACKEND"),
        include=[
            "app.tasks.user",
            "app.tasks.auth",
            "app.tasks.budget",
            "app.tasks.recurring_transaction",
            "app.tasks.report",
            "app.tasks.cleanup",
        ],
    )

    # Use Redis URL from environment if available
    celery.conf.broker_url = (
        app.config.get("CELERY_BROKER_URL") if app else "redis://localhost:6379/0"
    )
    celery.conf.result_backend = (
        app.config.get("CELERY_RESULT_BACKEND") if app else "redis://localhost:6379/0"
    )

    # Configure Celery
    celery.conf.update(
        task_serializer="json",
        accept_content=["json"],
        result_serializer="json",
        timezone="UTC",
        task_track_started=True,
        worker_max_tasks_per_child=1000,
        task_acks_late=True,
        broker_connection_retry_on_startup=True,
    )
    celery.conf.update(
        worker_hijack_root_logger=False,
    )
    # Configure Celery Beat Schedule
    celery.conf.beat_schedule = {
        "process-recurring-transactions": {
            "task": "process_recurring_transactions",
            "schedule": crontab(minute="*/5"),
        },
    }
    celery.conf.beat_schedule = {
        "hard-delete-soft-deleted-items-daily": {
            "task": "hard_delete_soft_deleted_items",
            "schedule": crontab(hour=0, minute=0),  # Runs daily at midnight UTC
        },
    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            if app:
                with app.app_context():
                    return self.run(*args, **kwargs)
            else:
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery


# Create a celery instance without Flask app for task definitions
celery = make_celery()
