# MODULE: Complaint Management (Part 2) - this file belongs to the code for this module.
# Asynchronous email outbox queuing, SMTP background dispatch worker, and console logger backend.

import os
import smtplib
import asyncio
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple, Optional
from backend.app.db import get_database
from backend.app.config import settings
from backend.app.notifications.templates.email_templates import render_template

logger = logging.getLogger("notifications")


async def notify(
    event: str,
    ticket_id: str,
    recipients: List[str],
    context: Dict[str, Any],
    channels: Tuple[str, ...] = ("email",)
) -> None:
    """Queues asynchronous notification outbox entries across channels.

    Args:
        event: Domain event key (e.g. 'complaint_registered').
        ticket_id: Associated 12-digit ticket ID string.
        recipients: List of target recipient email addresses.
        context: Placeholder dictionary for email body template rendering.
        channels: Tuple of channels to dispatch (default: ('email',)).
    """
    if "email" not in channels or not recipients:
        return

    db = get_database()
    context["ticket_id"] = ticket_id
    context["public_url"] = getattr(settings, "PUBLIC_BASE_URL", "http://localhost:5173")

    subject, text_body, html_body = render_template(event, context)

    # De-duplicate recipients
    clean_recipients = list(set([r.strip().lower() for r in recipients if r and r.strip()]))

    for recipient in clean_recipients:
        # If EMAIL_BACKEND is console in development, print immediately
        email_backend = getattr(settings, "EMAIL_BACKEND", "console").lower()
        app_env = getattr(settings, "APP_ENV", "development").lower()

        if email_backend == "console" and app_env == "development":
            logger.info("=" * 60)
            logger.info(f"[CONSOLE EMAIL] Event: {event} | To: {recipient}")
            logger.info(f"Subject: {subject}")
            logger.info("-" * 60)
            logger.info(text_body)
            logger.info("=" * 60)

        outbox_doc = {
            "event": event,
            "ticket_id": ticket_id,
            "to_email": recipient,
            "to_role": context.get("to_role", "RECIPIENT"),
            "subject": subject,
            "html": html_body,
            "text": text_body,
            "status": "PENDING",
            "attempts": 0,
            "next_attempt_at": datetime.utcnow(),
            "last_error": None,
            "created_at": datetime.utcnow(),
            "sent_at": None
        }
        await db.email_outbox.insert_one(outbox_doc)


def _send_smtp_email_sync(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    """Synchronous SMTP email sender helper executed in worker thread."""
    host = getattr(settings, "SMTP_HOST", "localhost")
    port = int(getattr(settings, "SMTP_PORT", 25))
    user = getattr(settings, "SMTP_USER", "")
    password = getattr(settings, "SMTP_PASSWORD", "")
    use_tls = getattr(settings, "SMTP_USE_TLS", False)
    from_email = getattr(settings, "EMAIL_FROM", "noreply@mnnit.ac.in")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = from_email
    msg["To"] = to_email

    msg.attach(MIMEText(text_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    with smtplib.SMTP(host, port, timeout=10) as server:
        if use_tls:
            server.starttls()
        if user and password:
            server.login(user, password)
        server.sendmail(from_email, [to_email], msg.as_string())


async def email_outbox_worker_loop():
    """Background loop sending up to 20 PENDING email messages every 10 seconds."""
    logger.info("[EmailOutboxWorker] Starting background email outbox loop...")

    while True:
        try:
            db = get_database()
            now_dt = datetime.utcnow()

            # Query up to 20 PENDING emails due for delivery
            cursor = db.email_outbox.find({
                "status": "PENDING",
                "next_attempt_at": {"$lte": now_dt}
            }).limit(20)

            email_backend = getattr(settings, "EMAIL_BACKEND", "console").lower()

            async for email_doc in cursor:
                doc_id = email_doc["_id"]
                attempts = email_doc.get("attempts", 0) + 1
                to_email = email_doc["to_email"]
                subject = email_doc["subject"]
                text_body = email_doc.get("text", "")
                html_body = email_doc.get("html", "")

                if email_backend == "console":
                    # Mark SENT immediately in console mode
                    await db.email_outbox.update_one(
                        {"_id": doc_id},
                        {
                            "$set": {
                                "status": "SENT",
                                "sent_at": datetime.utcnow(),
                                "attempts": attempts,
                                "html": None,
                                "text": None
                            }
                        }
                    )
                    continue

                # SMTP Mode
                try:
                    # Run sync SMTP send in executor thread
                    loop = asyncio.get_running_loop()
                    await loop.run_in_executor(
                        None,
                        _send_smtp_email_sync,
                        to_email,
                        subject,
                        text_body,
                        html_body
                    )

                    # On success: Purge html and text bodies for security, keep metadata
                    await db.email_outbox.update_one(
                        {"_id": doc_id},
                        {
                            "$set": {
                                "status": "SENT",
                                "sent_at": datetime.utcnow(),
                                "attempts": attempts,
                                "html": None,
                                "text": None
                            }
                        }
                    )
                    logger.info(f"[EmailOutboxWorker] Successfully sent email to '{to_email}' for ticket '{email_doc.get('ticket_id')}'.")

                except Exception as err:
                    # Handle failed attempt with exponential backoff (1m, 5m, 30m)
                    backoff_minutes = [1, 5, 30]
                    next_backoff = backoff_minutes[min(attempts - 1, len(backoff_minutes) - 1)]
                    new_next_attempt = datetime.utcnow() + timedelta(minutes=next_backoff)

                    new_status = "FAILED" if attempts >= 4 else "PENDING"
                    await db.email_outbox.update_one(
                        {"_id": doc_id},
                        {
                            "$set": {
                                "attempts": attempts,
                                "status": new_status,
                                "next_attempt_at": new_next_attempt,
                                "last_error": str(err)
                            }
                        }
                    )
                    logger.error(f"[EmailOutboxWorker] Failed sending email to '{to_email}' (attempt {attempts}/4): {err}")

        except Exception as loop_err:
            logger.error(f"[EmailOutboxWorker] Exception in outbox worker loop: {loop_err}", exc_info=True)

        await asyncio.sleep(10)
