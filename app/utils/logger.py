import logging
import logging.handlers
import os
import smtplib

# Create logs directory if it doesn't exist
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Suppress SMTP logs from appearing in the terminal
logging.getLogger("smtplib").setLevel(logging.WARNING)  # Adjust this as needed
logging.getLogger("email").setLevel(logging.WARNING)  # Suppress email-related logs

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # This is the level for your application's logs (can be DEBUG for more details)
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),  # Console handler
        logging.handlers.RotatingFileHandler(
            os.path.join(LOG_DIR, "app.log"),
            maxBytes=1 * 1024 * 1024,  # 1 MB (1 * 1024 KB * 1024 bytes)
            backupCount=5,
        ),  # File handler if needed
    ],
)

# Create logger instance
logger = logging.getLogger(__name__)


smtplib.SMTP.debuglevel = 0
