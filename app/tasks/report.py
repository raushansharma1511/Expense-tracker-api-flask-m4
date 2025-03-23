import os
import csv
import tempfile
from datetime import datetime
from weasyprint import HTML
from flask import render_template, current_app
from flask_mail import Message
from app.extensions import mail

from app.services.report import (
    parse_and_validate_dates,
    get_transactions_query,
    get_interwallet_transactions_query,
    calculate_transaction_totals,
)
from app.utils.logger import logger
from app.celery_app import celery
from app.models.transaction import Transaction
from app.models.interwallet_transaction import InterWalletTransaction
from app.models.user import User


@celery.task(name="generate_and_send_export", bind=True, max_retries=3)
def generate_and_send_export(
    self, current_user_id, target_user_email, query_params, export_format
):
    """Generate and email transaction export in PDF or CSV format"""
    try:

        # Get user
        user = User.query.get(current_user_id)
        target_user = User.query.filter_by(email=target_user_email).first()

        # Parse and validate dates
        start_date, end_date = parse_and_validate_dates(
            query_params.get("start_date"), query_params.get("end_date")
        )

        # Get transaction data for the date range
        transaction_query = get_transactions_query(
            user=user,
            role=user.role.value,
            start_date=start_date,
            end_date=end_date,
            query_params=query_params,
        )

        interwallet_query = get_interwallet_transactions_query(
            user=user,
            role=user.role.value,
            start_date=start_date,
            end_date=end_date,
            query_params=query_params,
        )

        total_credit, total_debit = calculate_transaction_totals(transaction_query)

        # Get transactions and sort by date (newest first)
        transactions = transaction_query.order_by(
            Transaction.transaction_at.desc()
        ).all()

        interwallet_transactions = interwallet_query.order_by(
            InterWalletTransaction.transaction_at.desc()
        ).all()

        # Generate file in requested format
        if export_format == "pdf":
            file_path = generate_pdf(
                target_user,
                transactions,
                interwallet_transactions,
                total_credit,
                total_debit,
                start_date,
                end_date,
            )
        else:
            file_path = generate_csv(
                target_user,
                transactions,
                interwallet_transactions,
                start_date,
                end_date,
            )

        if not file_path:
            logger.error(f"Failed to generate {export_format} export")
            return False

        # Send email with export file
        send_export_email(
            user_name=target_user.name,
            user_email=target_user_email,
            file_path=file_path,
            export_format=export_format,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
        )

        # Delete temporary file
        try:
            os.remove(file_path)
        except Exception as e:
            logger.warning(f"Failed to delete temporary file {file_path}: {str(e)}")

        return True

    except Exception as e:
        logger.error(f"Error generating export: {str(e)}")
        if self.request.retries < self.max_retries:
            self.retry(exc=e, countdown=60 * (self.request.retries + 1))
        return False


def generate_pdf(
    user,
    transactions,
    interwallet_transactions,
    total_credit,
    total_debit,
    start_date,
    end_date,
):
    """Generate PDF export of transactions"""
    try:
        # Create a temp file
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"transactions_{user.id}_{timestamp}.pdf"
        file_path = os.path.join(temp_dir, filename)

        # Generate HTML with transaction data
        html_content = render_template(
            "report/transaction_export.html",
            user=user,
            transactions=transactions,
            interwallet_transactions=interwallet_transactions,
            total_credit=total_credit,
            total_debit=total_debit,
            start_date=start_date.strftime("%Y-%m-%d"),
            end_date=end_date.strftime("%Y-%m-%d"),
            generation_date=datetime.now().strftime("%Y-%m-%d %H:%M"),
        )

        # Convert HTML to PDF
        HTML(string=html_content).write_pdf(file_path)

        logger.info(f"Generated PDF export at {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error generating PDF: {str(e)}")
        return None


def generate_csv(user, transactions, interwallet_transactions, start_date, end_date):
    """Generate CSV export of transactions"""
    try:
        # Create a temp file
        temp_dir = tempfile.gettempdir()
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"transactions_{user.id}_{timestamp}.csv"
        file_path = os.path.join(temp_dir, filename)

        with open(file_path, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # File metadata
            writer.writerow(["Transaction Export"])
            writer.writerow(["User", user.name])
            writer.writerow(
                [
                    "Date Range",
                    f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
                ]
            )
            writer.writerow(["Generated On", datetime.now().strftime("%Y-%m-%d %H:%M")])
            writer.writerow([])

            # Regular transactions header
            writer.writerow(["TRANSACTIONS"])
            writer.writerow(["Type", "Amount", "Category", "Wallet", "Date & Time"])

            # Regular transactions data
            for txn in transactions:
                writer.writerow(
                    [
                        txn.type.value,
                        str(txn.amount),
                        txn.category.name,
                        txn.wallet.name,
                        txn.transaction_at.strftime("%Y-%m-%d %H:%M"),
                    ]
                )

            writer.writerow([])

            # Interwallet transactions header
            writer.writerow(["INTERWALLET TRANSFERS"])
            writer.writerow(["From Wallet", "To Wallet", "Amount", "Date & Time"])

            # Interwallet transactions data
            for transfer in interwallet_transactions:
                writer.writerow(
                    [
                        transfer.source_wallet.name,
                        transfer.destination_wallet.name,
                        str(transfer.amount),
                        transfer.transaction_at.strftime("%Y-%m-%d %H:%M"),
                    ]
                )

        logger.info(f"Generated CSV export at {file_path}")
        return file_path

    except Exception as e:
        logger.error(f"Error generating CSV: {str(e)}")
        return None


def send_export_email(
    user_name, user_email, file_path, export_format, start_date, end_date
):
    """Send email with export attachment using the existing email helper"""
    try:
        # Read the file
        with open(file_path, "rb") as f:
            file_content = f.read()

        # Determine content type
        content_type = "application/pdf" if export_format == "pdf" else "text/csv"

        # Create email context
        context = {
            "user_name": user_name,
            "export_format": export_format.upper(),
            "date_range": f"{start_date} to {end_date}",
        }

        # Render template
        html_content = render_template(
            "emails/report/export_notification.html", **context
        )

        # Create message
        msg = Message(
            f"Your Transaction Export ({start_date} to {end_date})",
            recipients=[user_email],
            html=html_content,
        )

        # Attach file
        filename = os.path.basename(file_path)
        msg.attach(filename=filename, content_type=content_type, data=file_content)

        # Send
        mail.send(msg)

        logger.info(f"Sent export email to {user_email}")
        return True

    except Exception as e:
        logger.error(f"Error sending export email: {str(e)}")
        return False
