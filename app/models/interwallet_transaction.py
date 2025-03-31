from decimal import Decimal
from datetime import datetime, timezone
from app.extensions import db
from app.models.base import BaseModel


class InterWalletTransaction(BaseModel):
    """Model for transfers between wallets of the same user"""

    __tablename__ = "interwallet_transactions"

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    description = db.Column(db.Text, nullable=True)

    # Foreign keys
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    source_wallet_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    destination_wallet_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("wallets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    user = db.relationship(
        "User",
        backref=db.backref(
            "interwallet_transactions", lazy="dynamic", cascade="all, delete"
        ),
    )

    source_wallet = db.relationship(
        "Wallet",
        foreign_keys=[source_wallet_id],
        backref=db.backref("source_transactions", lazy="dynamic"),
    )

    destination_wallet = db.relationship(
        "Wallet",
        foreign_keys=[destination_wallet_id],
        backref=db.backref("destination_transactions", lazy="dynamic"),
    )

    def __repr__(self):
        return f"<InterWalletTransaction {self.user_id} | {self.source_wallet_id} -> {self.destination_wallet_id} | {self.amount}>"

    @property
    def get_amount(self):
        """Return amount as a Python Decimal object"""
        return Decimal(str(self.amount))

    def apply_to_wallets(self):
        """Apply this transaction to the associated wallets"""
        self.source_wallet.update_balance(-self.get_amount)
        self.destination_wallet.update_balance(self.get_amount)

    def reverse_from_wallets(self):
        """Reverse this transaction's effect on the associated wallets"""
        self.source_wallet.update_balance(self.get_amount)
        self.destination_wallet.update_balance(-self.get_amount)
