"""E-mail helpers.

In development the emails are *printed to the console* with a clickable link so
the verification / reset flow can be tested without SMTP credentials. Once the
MAIL_* environment variables are set, real emails are sent through smtplib.
"""
import logging
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import current_app, url_for

logger = logging.getLogger(__name__)


def send_email(to, subject, body_html, body_text=None):
    """Send an email; fall back to console logging when SMTP is unconfigured."""
    app = current_app
    body_text = body_text or "Please view this email in an HTML client."

    if not app.config.get("MAIL_USERNAME") or not app.config.get("MAIL_PASSWORD"):
        logger.info(
            "\n===== [PLACEHOLDER EMAIL] =====\nTo: %s\nSubject: %s\n\n%s\n===== END EMAIL =====\n",
            to, subject, body_html,
        )
        return

    def _send():
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = app.config["MAIL_DEFAULT_SENDER"]
        msg["To"] = to
        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        with smtplib.SMTP(
            app.config["MAIL_SERVER"], app.config["MAIL_PORT"]
        ) as server:
            if app.config["MAIL_USE_TLS"]:
                server.starttls()
            if app.config.get("MAIL_USERNAME"):
                server.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
            server.sendmail(msg["From"], [to], msg.as_string())

    threading.Thread(target=_send, daemon=True).start()


def send_verification_email(user, token):
    """Email a verification link to a freshly registered user."""
    link = url_for("auth.verify_email", token=token, _external=True)
    body_html = f"""
    <h3>Welcome to {current_app.config['APP_NAME']}!</h3>
    <p>Hi {user.username},</p>
    <p>Please verify your email by clicking the button below:</p>
    <p><a href="{link}" style="padding:10px 18px;background:#0d6efd;color:#fff;text-decoration:none;border-radius:6px;">Verify Email</a></p>
    <p>Or copy this link: <a href="{link}">{link}</a></p>
    <p>If you didn't create this account, you can safely ignore this email.</p>
    """
    send_email(user.email, f"Verify your email - {current_app.config['APP_NAME']}", body_html)


def send_password_reset_email(user, token):
    """Email a password reset link."""
    link = url_for("auth.reset_password", token=token, _external=True)
    body_html = f"""
    <h3>Reset your password</h3>
    <p>Hi {user.username},</p>
    <p>We received a request to reset your password. Click below to choose a new one:</p>
    <p><a href="{link}" style="padding:10px 18px;background:#0d6efd;color:#fff;text-decoration:none;border-radius:6px;">Reset Password</a></p>
    <p>Or copy this link: <a href="{link}">{link}</a></p>
    <p>This link expires in 1 hour. If you didn't request it, ignore this email.</p>
    """
    send_email(user.email, f"Reset your password - {current_app.config['APP_NAME']}", body_html)
