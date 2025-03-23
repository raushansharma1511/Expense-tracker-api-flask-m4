import uuid
from decimal import Decimal
from app.extensions import db
from app.models.base import BaseModel


class Wallet(BaseModel):
    """Wallet model representing a user's financial account"""

    __tablename__ = "wallets"

    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Numeric(15, 2), default=0.00, nullable=False)
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    # Define relationship with User
    user = db.relationship(
        "User", backref=db.backref("wallets", lazy="dynamic", cascade="all, delete")
    )

    def __repr__(self):
        return f"<Wallet {self.name} (User: {self.user_id})>"

    @property
    def get_balance(self):
        """Return balance as a Python Decimal object"""
        return Decimal(str(self.balance))

    def update_balance(self, amount):
        """
        Update wallet balance by adding the given amount
        Positive amount adds to balance, negative subtracts
        """
        self.balance = self.get_balance + Decimal(str(amount))
        return self.balance
