from datetime import datetime
from app.celery_app import celery
from app.extensions import db
from app.models.recurring_transaction import RecurringTransaction
from app.models.transaction import Transaction
from app.models.wallet import Wallet
from app.utils.logger import logger
from app.utils.email_helper import send_templated_email
from app.utils.enums import TransactionType
from app.services.recurring_transaction import calculate_next_execution_date
from app.services.manage_budget import update_budget_on_transaction_created


@celery.task(name="process_recurring_transactions", bind=True, max_retries=3)
def process_recurring_transactions(self):
    """Process all due recurring transactions"""
    try:
        now = datetime.now()
        logger.info(f"Processing recurring transactions due before {now}")

        # Get all non-deleted recurring transactions that are due
        due_transactions = RecurringTransaction.query.filter(
            RecurringTransaction.next_execution_at <= now,
            RecurringTransaction.is_deleted == False,
        ).all()

        logger.info(f"Found {len(due_transactions)} due recurring transactions")

        for recurring_txn in due_transactions:
            try:
                result = process_single_transaction(recurring_txn.id)

            except Exception as e:
                logger.error(
                    f"Error processing recurring transaction {recurring_txn.id}: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error in process_recurring_transactions task: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        return False


def process_single_transaction(recurring_transaction_id):
    """
    Process a single recurring transaction within a database transaction.

    Returns:
      - True if processed successfully
      - False if skipped
      - Tuple with error info if error occurred
    """
    try:
        # Get recurring transaction with fresh data
        recurring_txn = RecurringTransaction.query.get(recurring_transaction_id)

        if not recurring_txn:
            logger.warning(
                f"Recurring transaction {recurring_transaction_id} not found"
            )
            return False

        # Check if related objects are deleted or invalid
        if (
            recurring_txn.user.is_deleted
            or recurring_txn.wallet.is_deleted
            or recurring_txn.category.is_deleted
            or (
                recurring_txn.end_at
                and recurring_txn.end_at.date() < recurring_txn.next_execution_at.date()
            )
        ):
            logger.info(
                f"Skipping recurring transaction {recurring_txn.id} - invalid state or related objects"
            )
            recurring_txn.is_deleted = True
            db.session.commit()
            return False

        # Lock the wallet for update to prevent race conditions
        wallet = (
            Wallet.query.filter_by(id=recurring_txn.wallet_id).with_for_update().first()
        )

        wallet = Wallet.query.get(recurring_txn.wallet_id)

        # Create the actual transaction
        new_transaction = Transaction(
            user_id=recurring_txn.user_id,
            wallet_id=recurring_txn.wallet_id,
            category_id=recurring_txn.category_id,
            type=recurring_txn.type,
            amount=recurring_txn.amount,
            description=recurring_txn.description or "Recurring transaction",
            transaction_at=recurring_txn.next_execution_at,
        )

        db.session.add(new_transaction)
        db.session.flush()  # Get the ID assigned

        # Update wallet balance directly
        if recurring_txn.type == TransactionType.CREDIT:
            wallet.balance += recurring_txn.amount
        else:
            wallet.balance -= recurring_txn.amount
            update_budget_on_transaction_created(new_transaction)

        # Update recurring transaction
        recurring_txn.last_executed_at = recurring_txn.next_execution_at

        next_date = calculate_next_execution_date(recurring_txn)
        recurring_txn.next_execution_at = next_date

        # Commit the transaction
        db.session.commit()

        # Schedule email notification
        send_recurring_transaction_email.delay(recurring_txn.id, new_transaction.id)

        logger.info(
            f"Successfully processed recurring transaction {recurring_txn.id}, created transaction {new_transaction.id}"
        )
        return True

    except Exception as e:
        db.session.rollback()
        logger.error(
            f"Error processing recurring transaction {recurring_transaction_id}: {str(e)}"
        )
        return {"error": f"Failed to process recurring transaction: {str(e)}"}, 500


@celery.task(name="send_recurring_transaction_email")
def send_recurring_transaction_email(recurring_txn_id, transaction_id):
    """
    Send email notification about processed recurring transaction
    """
    try:
        # Load the recurring transaction and the created transaction
        recurring_txn = RecurringTransaction.query.get(recurring_txn_id)
        transaction = Transaction.query.get(transaction_id)

        if not recurring_txn or not transaction:
            logger.error(
                f"Could not find recurring transaction {recurring_txn_id} or transaction {transaction_id} for email notification"
            )
            return False

        # Get user email
        user = recurring_txn.user
        if not user or not user.email:
            logger.error(
                f"Could not find user or email for recurring transaction {recurring_txn_id}"
            )
            return False

        amount = float(transaction.amount)
        formatted_amount = f"Rs {amount:.2f}"

        # Send email using your helper function
        send_templated_email(
            recipient=user.email,
            subject="Recurring Transaction Processed",
            template="emails/recurring_transaction/transaction_notification.html",
            transaction_id=str(transaction.id),
            transaction_type=transaction.type.value.capitalize(),
            amount=formatted_amount,
            category_name=transaction.category.name,
            wallet_name=transaction.wallet.name,
            description=transaction.description,
            transaction_date=transaction.transaction_at.strftime("%Y-%m-%d"),
            frequency=recurring_txn.frequency.value.capitalize(),
            next_execution=(
                recurring_txn.next_execution_at.strftime("%Y-%m-%d")
                if recurring_txn.next_execution_at.date() < recurring_txn.end_at.date()
                else "No future executions"
            ),
        )

        logger.info(
            f"Sent recurring transaction processed email for transaction {transaction_id}"
        )
        return True

    except Exception as e:
        logger.error(f"Error sending recurring transaction processed email: {str(e)}")
        return False
