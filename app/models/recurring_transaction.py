from app.extensions import db
from app.models.base import BaseModel
from app.utils.enums import (
    TransactionType,
    TransactionFrequency,
)


class RecurringTransaction(BaseModel):
    """Model for recurring transactions"""

    __tablename__ = "recurring_transactions"

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.Enum(TransactionType, name="transaction_type"), nullable=False)

    frequency = db.Column(
        db.Enum(TransactionFrequency, name="transaction_frequency"), nullable=False
    )
    start_at = db.Column(db.DateTime, nullable=False)
    end_at = db.Column(db.DateTime, nullable=True, default=None)
    next_execution_at = db.Column(db.DateTime, nullable=False)
    last_executed_at = db.Column(db.DateTime, nullable=True, default=None)

    # Foreign keys
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    wallet_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    user = db.relationship(
        "User",
        backref=db.backref(
            "recurring_transactions", lazy="dynamic", cascade="all, delete"
        ),
    )
    wallet = db.relationship(
        "Wallet",
        backref=db.backref(
            "recurring_transactions", lazy="dynamic", cascade="all, delete"
        ),
    )
    category = db.relationship(
        "Category",
        backref=db.backref(
            "recurring_transactions", lazy="dynamic", cascade="all, delete"
        ),
    )
