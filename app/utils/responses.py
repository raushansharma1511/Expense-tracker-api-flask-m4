from flask import Response
from app.utils.logger import logger


def validation_error_response(error):
    if isinstance(error.messages, dict):
        formatted_errors = {
            field: messages[0] if isinstance(messages, list) else messages
            for field, messages in error.messages.items()
        }
    elif isinstance(error.messages, list):
        formatted_errors = error.messages[0] if len(error.messages) > 0 else "error"

    logger.warning(f"Data validation error: {formatted_errors}")
    return {"error": formatted_errors}, 400
