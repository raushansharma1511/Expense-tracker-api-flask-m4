from app.models.budget import Budget
from app.utils.logger import logger
from app.extensions import db
from app.tasks.budget import check_budget_thresholds


def find_matching_budget(transaction):
    """
    Find a budget matching a transaction's user, category, month and year.
    """

    # Extract transaction date components
    txn_date = transaction.transaction_at
    month = txn_date.month
    year = txn_date.year

    # Find matching budget
    budget = Budget.query.filter(
        Budget.user_id == transaction.user_id,
        Budget.category_id == transaction.category_id,
        Budget.month == month,
        Budget.year == year,
        Budget.is_deleted == False,
    ).first()

    return budget


def update_budget_on_transaction_created(transaction):
    """
    Update budget when a transaction is created.
    """
    try:
        budget = find_matching_budget(transaction)
        if not budget:
            logger.info(f"No budget found for transaction {transaction.id}")
            return

        # Add transaction amount to budget spent_amount
        budget.spent_amount += transaction.amount

        db.session.commit()

        logger.info(
            f"Updated budget {budget.id} spent_amount after transaction created"
        )
        # Check if budget thresholds are reached
        check_budget_thresholds.delay(budget.id)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating budget on transaction created: {str(e)}")
        raise e


def update_budget_on_transaction_updated(transaction, old_transaction):
    """
    Update budget when a transaction is updated.
    """
    try:
        # Check if any relevant fields changed
        amount_changed = transaction.amount != old_transaction.amount
        category_changed = transaction.category_id != old_transaction.category_id
        date_changed = (
            transaction.transaction_at.month != old_transaction.transaction_at.month
            or transaction.transaction_at.year != old_transaction.transaction_at.year
        )

        if not (amount_changed or category_changed or date_changed):
            return

        old_budget = find_matching_budget(old_transaction)

        if old_budget:
            old_budget.spent_amount -= old_transaction.amount
            logger.info(
                f"Reduced old budget {old_budget.id} spent_amount by {old_transaction.amount}"
            )

        db.session.flush()

        current_budget = find_matching_budget(transaction)

        if current_budget:
            current_budget.spent_amount += transaction.amount
            logger.info(
                f"Increased current budget {current_budget.id} spent_amount by {transaction.amount}"
            )

        db.session.commit()

        if current_budget:
            check_budget_thresholds.delay(current_budget.id)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating budget on transaction updated: {str(e)}")
        raise e


def update_budget_on_transaction_deleted(transaction):
    """
    Update budget when a transaction is deleted.
    """
    try:
        # Find matching budget
        budget = find_matching_budget(transaction)
        if not budget:
            logger.debug(f"No budget found for transaction {transaction.id}")
            return

        budget.spent_amount -= transaction.amount

        db.session.commit()

        logger.info(
            f"Updated budget {budget.id} spent_amount of transaction {transaction.id}"
        )
        check_budget_thresholds.delay(budget.id)

    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating budget on transaction: {str(e)}")
        raise e
