from app.extensions import db, bcrypt
from app.models.base import BaseModel
from app.utils.logger import logger
from app.utils.enums import UserRole, Gender
import uuid


class ParentChildRelation(db.Model):
    """Model to store parent-child relationships between users"""

    __tablename__ = "parent_child_relations"

    id = db.Column(db.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    child_id = db.Column(
        db.UUID(as_uuid=True),
        db.ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_deleted = db.Column(db.Boolean, default=False)

    parent_user = db.relationship(
        "User",
        foreign_keys=[parent_id],
        backref=db.backref("children", lazy="dynamic", cascade="all, delete"),
    )
    child_user = db.relationship(
        "User",
        foreign_keys=[child_id],
        backref=db.backref("parent", uselist=False, cascade="all, delete"),
    )

    # Prevent duplicate relationships between same users
    __table_args__ = (
        db.UniqueConstraint("parent_id", "child_id", name="unique_parent_child"),
    )

    def __repr__(self):
        return f"<ParentChildRelation parent:{self.parent_id} -> child:{self.child_id}>"


class User(BaseModel):
    """User model with all its detail"""

    __tablename__ = "users"

    username = db.Column(db.String(120), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    role = db.Column(
        db.Enum(UserRole),
        nullable=False,
        default=UserRole.USER,
    )
    date_of_birth = db.Column(db.Date, nullable=True)
    gender = db.Column(db.Enum(Gender), nullable=True)

    def set_password(self, password):
        """Hashes and sets the password."""
        self.password = bcrypt.generate_password_hash(password).decode("utf-8")
        logger.info(f"Password set for user {self.email}")

    def check_password(self, password):
        """Checks the hashed password."""
        return bcrypt.check_password_hash(self.password, password)

    def get_child(self):
        """Get all child users for this parent"""
        # Filter children by deletion status based on the parameter
        relation = self.children.filter_by(is_deleted=False).first()

        # Return the child user object if relation exists, otherwise None
        return relation.child_user if relation else None

    def has_child(self):
        """Check if user has any active children"""
        return self.children.filter_by(is_deleted=False).count() > 0

    def get_parent(self):
        """Get parent user for this child"""
        return self.parent.parent_user if self.parent else None

    @property
    def is_admin(self):
        """Check if user is admin"""
        return self.role == UserRole.ADMIN

    @property
    def is_child_user(self):
        """Check if user is a child user"""
        return self.role == UserRole.CHILD_USER

    def __repr__(self):
        return f"<User {self.username} {self.email} {self.name}>"
