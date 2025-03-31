import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration class."""

    SECRET_KEY = os.getenv("SECRET_KEY", "secret-key")
    SQLALCHEMY_DATABASE_URI = (
        f"postgresql://"
        f"{os.getenv('DB_USER')}:"
        f"{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/"
        f"{os.getenv('DB_NAME')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False  # Required for Flask-SQLAlchemy
    FLASK_ENV = os.getenv("FLASK_ENV")
    FLASK_DEBUG = os.getenv("FLASK_DEBUG")
    MAIL_SERVER = os.getenv("MAIL_SERVER")
    MAIL_PORT = int(os.getenv("MAIL_PORT"))
    MAIL_USE_TLS = os.getenv("MAIL_USE_TLS", "True") == "True"
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")
    MAIL_DEFAULT_SENDER = os.getenv("MAIL_DEFAULT_SENDER")
    MAIL_DEBUG = os.getenv("MAIL_DEBUG", "False") == "True"

    # Celery
    CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL")
    CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND")

    REDIS_URL = os.getenv("REDIS_URL")

    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "jwt-secret-key-change-me")
    JWT_ACCESS_TOKEN_EXPIRES = (
        int(os.getenv("JWT_ACCESS_TOKEN_EXPIRES", "60")) * 60
    )  # minutes to seconds
    JWT_REFRESH_TOKEN_EXPIRES = (
        int(os.getenv("JWT_REFRESH_TOKEN_EXPIRES", "30")) * 24 * 60 * 60
    )  # days to seconds

    # Security Timeouts
    PASSWORD_RESET_LINK_VALIDITY = int(os.getenv("PASSWORD_RESET_LINK_VALIDITY", "300"))
    PASSWORD_RESET_LINK_SEND_RATE_LIMIT = int(
        os.getenv("PASSWORD_RESET_LINK_SEND_RATE_LIMIT", "300")
    )
    ACCCOUNT_VERIFICATION_LINK_VALIDITY = int(
        os.getenv("ACCCOUNT_VERIFICATION_LINK_VALIDITY", "300")
    )
    ACCOUNT_VERIFICATION_LINK_SEND_RATE_LIMIT = int(
        os.getenv("ACCOUNT_VERIFICATION_LINK_SEND_RATE_LIMIT", "300")
    )
    EMAIL_CHANGE_TOKEN_VALIDITY = int(
        os.getenv("EMAIL_CHANGE_TOKEN_VALIDITY", "43200")
    )  # 12 hours in seconds
    EMAIL_CHANGE_TOKEN_RESEND = int(os.getenv("EMAIL_CHANGE_TOKEN_RESEND", "300"))
    OTP_VALID_FOR = int(os.getenv("OTP_VALID_FOR", "300"))


class TestConfig(Config):
    """Test configuration."""

    TESTING = True

    # Use a separate database for testing
    SQLALCHEMY_DATABASE_URI = f"postgresql://{os.getenv('DB_USER', 'mac')}:{os.getenv('DB_PASSWORD', '1234')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '5432')}/{os.getenv('TEST_DB_NAME', 'expense_tracker_test')}"

    # JWT shorter expiration for faster testing
    JWT_ACCESS_TOKEN_EXPIRES = 300  # 5 minutes
    JWT_REFRESH_TOKEN_EXPIRES = 600  # 10 minutes

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Email configuration for testing
    MAIL_SUPPRESS_SEND = True

    # Use Redis database 15 for testing (separating from dev/prod Redis)
    REDIS_DB = 15

    # Run Celery tasks synchronously for testing
    CELERY_TASK_ALWAYS_EAGER = True
