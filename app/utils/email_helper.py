from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail
from datetime import datetime


def send_templated_email(recipient, subject, template, **context):
    """
    Send an email using a template.

    Args:
        recipient (str): Recipient's email address
        subject (str): Email subject
        template (str): Path to template file
        **context: Context variables for the template
    """
    # Add current year for copyright in footer
    context["current_year"] = datetime.now().year

    # Render HTML content
    html_content = render_template(template, **context)

    # Create message
    msg = Message(subject=subject, recipients=[recipient], html=html_content)

    # Send email
    mail.send(msg)
