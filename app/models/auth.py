from app.extensions import db
import uuid
from datetime import datetime, timezone


class ActiveAccessToken(db.Model):
    __tablename__ = "active_access_tokens"

    def utc_now():
        """Return the current UTC time with timezone awareness"""
        return datetime.now(timezone.utc)

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    access_token = db.Column(db.String(500), unique=True, nullable=False)
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at = db.Column(db.DateTime, default=utc_now)

    # Define relationship with User
    user = db.relationship(
        "User", backref=db.backref("tokens", lazy="dynamic", cascade="all, delete")
    )

    def __repr__(self):
        return f"Token for {self.user.username}"
