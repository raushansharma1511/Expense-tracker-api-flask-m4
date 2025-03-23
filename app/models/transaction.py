from decimal import Decimal
from datetime import datetime, timezone
from app.extensions import db
from app.models.base import BaseModel
from app.utils.enums import TransactionType


class Transaction(BaseModel):
    """Model for financial transactions"""

    __tablename__ = "transactions"

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    description = db.Column(db.Text, nullable=True)
    type = db.Column(db.Enum(TransactionType, name="transaction_type"), nullable=False)

    # Foreign keys
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    wallet_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
    )
    category_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Relationships
    user = db.relationship(
        "User",
        backref=db.backref("transactions", lazy="dynamic", cascade="all, delete"),
    )
    wallet = db.relationship(
        "Wallet",
        backref=db.backref("transactions", lazy="dynamic", cascade="all, delete"),
    )
    category = db.relationship(
        "Category",
        backref=db.backref("transactions", lazy="dynamic", cascade="all, delete"),
    )

    def __repr__(self):
        return f"<Transaction {self.user_id} | {self.wallet_id} | {self.type.value} {self.amount}>"

    @property
    def get_amount(self):
        """Return amount as a Python Decimal object"""
        return Decimal(str(self.amount))
