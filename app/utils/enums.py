import enum


class UserRole(enum.Enum):
    """Enum for user roles"""

    USER = "USER"
    CHILD_USER = "CHILD_USER"
    ADMIN = "ADMIN"


class Gender(enum.Enum):
    """Enum for user gender"""

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class TransactionType(enum.Enum):
    """Enum for transaction types"""

    CREDIT = "CREDIT"
    DEBIT = "DEBIT"


class TransactionFrequency(enum.Enum):
    """Enum for transaction frequency"""

    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"
