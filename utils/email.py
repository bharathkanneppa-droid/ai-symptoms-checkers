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

from utils.time import utcnow

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
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = app.config["MAIL_DEFAULT_SENDER"]
            msg["To"] = to
            msg.attach(MIMEText(body_text, "plain"))
            msg.attach(MIMEText(body_html, "html"))

            with smtplib.SMTP(
                app.config["MAIL_SERVER"], app.config["MAIL_PORT"], timeout=30
            ) as server:
                if app.config["MAIL_USE_TLS"]:
                    server.starttls()
                if app.config.get("MAIL_USERNAME"):
                    server.login(app.config["MAIL_USERNAME"], app.config["MAIL_PASSWORD"])
                server.sendmail(msg["From"], [to], msg.as_string())
            logger.info("Email sent to %s (subject: %s)", to, subject)
        except Exception:
            logger.exception("Failed to send email to %s (subject: %s)", to, subject)

    threading.Thread(target=_send, daemon=True).start()


def _branded_email(title, greeting, body_blocks, cta_text, cta_link, footer_note=""):
    """Render a simple branded HTML email with the app's teal theme."""
    app_name = current_app.config["APP_NAME"]
    blocks = "".join(f"<p style=\"margin:0 0 14px;line-height:1.6;color:#334155;\">{b}</p>" for b in body_blocks)
    return f"""
    <div style="background:#f0f7f6;padding:28px 12px;font-family:Arial,Helvetica,sans-serif;">
      <div style="max-width:520px;margin:0 auto;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e2ecea;">
        <div style="background:linear-gradient(120deg,#0d9488,#06b6d4);padding:22px 28px;">
          <h1 style="margin:0;color:#ffffff;font-size:20px;">{app_name}</h1>
          <p style="margin:4px 0 0;color:rgba(255,255,255,0.85);font-size:13px;">AI-powered healthcare, in your hands</p>
        </div>
        <div style="padding:26px 28px;">
          <h2 style="margin:0 0 14px;font-size:17px;color:#0f766e;">{title}</h2>
          <p style="margin:0 0 14px;color:#334155;">{greeting}</p>
          {blocks}
          <p style="margin:20px 0 0;text-align:center;">
            <a href="{cta_link}" style="display:inline-block;padding:11px 22px;background:linear-gradient(120deg,#0d9488,#06b6d4);color:#ffffff;text-decoration:none;border-radius:8px;font-weight:bold;">{cta_text}</a>
          </p>
          {f'<p style="margin:14px 0 0;font-size:12px;color:#64748b;">{footer_note}</p>' if footer_note else ''}
        </div>
        <div style="background:#f8fafc;padding:12px 28px;border-top:1px solid #e2ecea;font-size:11px;color:#94a3b8;">
          &copy; {utcnow().year} {app_name} — educational demo, not medical advice.
        </div>
      </div>
    </div>
    """


def send_verification_email(user, token):
    """Email a verification link to a freshly registered user."""
    link = url_for("auth.verify_email", token=token, _external=True)
    body_html = _branded_email(
        title="Verify your email",
        greeting=f"Hi {user.username},",
        body_blocks=[
            "Thanks for joining MediAssist AI. Please confirm your email address to activate your account.",
        ],
        cta_text="Verify Email",
        cta_link=link,
        footer_note=f"Or copy this link into your browser: {link}",
    )
    send_email(user.email, f"Verify your email - {current_app.config['APP_NAME']}", body_html)


def send_password_reset_email(user, token):
    """Email a password reset link."""
    link = url_for("auth.reset_password", token=token, _external=True)
    body_html = _branded_email(
        title="Reset your password",
        greeting=f"Hi {user.username},",
        body_blocks=[
            "We received a request to reset your password. Click below to choose a new one.",
            "If you didn't request this, you can safely ignore this email.",
        ],
        cta_text="Reset Password",
        cta_link=link,
        footer_note=f"This link expires in 1 hour. Or copy it: {link}",
    )
    send_email(user.email, f"Reset your password - {current_app.config['APP_NAME']}", body_html)
