import uuid
from app.extensions import db
from app.models.base import BaseModel
from app.utils.constants import CATEGORY_NAME_MAX_LENGTH as cat_name_len


class Category(BaseModel):
    """Category model to store categories of transactions"""

    __tablename__ = "categories"

    name = db.Column(db.String(cat_name_len), nullable=False)
    user_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_predefined = db.Column(db.Boolean, default=False)

    # Define relationship with User
    user = db.relationship(
        "User", backref=db.backref("categories", lazy="dynamic", cascade="all, delete")
    )

    def __repr__(self):
        return f"<Category {self.name}>"
