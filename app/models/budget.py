from decimal import Decimal
from datetime import date, timedelta
from app.extensions import db
from app.models.base import BaseModel


class Budget(BaseModel):
    """Model for budget table"""

    __tablename__ = "budgets"

    amount = db.Column(db.Numeric(10, 2), nullable=False)
    spent_amount = db.Column(db.Numeric(10, 2), nullable=False, default=Decimal(0.00))

    month = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)

    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    category_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("categories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    warning_notification_sent = db.Column(db.Boolean, nullable=False, default=False)
    exceeded_notification_sent = db.Column(db.Boolean, nullable=False, default=False)

    # Relationship
    user = db.relationship(
        "User", backref=db.backref("budgets", lazy="dynamic", cascade="all, delete")
    )
    category = db.relationship(
        "Category", backref=db.backref("budgets", lazy="dynamic", cascade="all, delete")
    )

    @property
    def remaining(self):
        """Calculate remaining budget"""
        return max(Decimal("0"), self.amount - self.spent_amount)

    @property
    def percentage_used(self):
        """Calculate percentage of budget used"""
        if self.amount == 0:
            return 100 if self.spent_amount > 0 else 0
        return min(100, int((self.spent_amount / self.amount) * 100))

    @property
    def is_exceeded(self):
        """Check if budget is exceeded"""
        return self.spent_amount > self.amount

    def __repr__(self):
        return f"<Budget {self.id}: {self.user_id} | {self.category_id} | {self.month}/{self.year}>"
