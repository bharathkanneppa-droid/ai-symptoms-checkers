"""Application configuration.

Environment variables (see .env.example) override defaults so the same
codebase runs locally on SQLite and in production on PostgreSQL (Render,
Railway, PythonAnywhere).
"""
import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

load_dotenv(BASE_DIR / ".env")


def _database_uri():
    """Prefer a provided PostgreSQL URL; fall back to local SQLite.

    Accepts DATABASE_URL plus the vars Vercel Postgres injects
    (POSTGRES_URL_NON_POOLING is preferred: it avoids the pgbouncer-style
    transaction pooling that breaks long-lived SQLAlchemy sessions).
    """
    uri = (
        os.environ.get("DATABASE_URL")
        or os.environ.get("POSTGRES_URL_NON_POOLING")
        or os.environ.get("POSTGRES_URL")
    )
    if uri:
        # SQLAlchemy 2.x expects the postgresql:// scheme, not postgres://
        return uri.replace("postgres://", "postgresql://", 1)
    return f"sqlite:///{BASE_DIR / 'medical.db'}"


class Config:
    # --- Core -----------------------------------------------------------------
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me-in-production")

    SQLALCHEMY_DATABASE_URI = _database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}

    # --- Auth / sessions --------------------------------------------------------
    REMEMBER_COOKIE_DURATION = timedelta(days=int(os.environ.get("REMEMBER_DAYS", 14)))
    REMEMBER_COOKIE_HTTPONLY = True

    # --- CSRF ---------------------------------------------------------------------
    WTF_CSRF_TIME_LIMIT = None

    # --- Mail (used by "email verification" / "forgot password" flows) ---------
    # Placeholder by default: emails are printed to the console. Configure SMTP
    # in production (see README -> Deployment).
    MAIL_SERVER = os.environ.get("MAIL_SERVER", "smtp.gmail.com")
    MAIL_PORT = int(os.environ.get("MAIL_PORT", 587))
    MAIL_USE_TLS = os.environ.get("MAIL_USE_TLS", "true").lower() == "true"
    MAIL_USE_SSL = os.environ.get("MAIL_USE_SSL", "false").lower() == "true"
    MAIL_USERNAME = os.environ.get("MAIL_USERNAME", "")
    MAIL_PASSWORD = os.environ.get("MAIL_PASSWORD", "")
    MAIL_DEFAULT_SENDER = os.environ.get("MAIL_DEFAULT_SENDER", "no-reply@medassist.local")
    EMAIL_VERIFICATION_REQUIRED = os.environ.get(
        "EMAIL_VERIFICATION_REQUIRED", "false"
    ).lower() == "true"

    # --- App details ----------------------------------------------------------------
    APP_NAME = "MediAssist AI"
    UPLOAD_FOLDER = BASE_DIR / "static" / "uploads"
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024

    # --- AI (Google Gemini) ---------------------------------------------------------
    # When GEMINI_API_KEY is set, the AI Doctor chat uses the live Gemini model.
    # Without it, the app falls back to the built-in rule-based symptom bot.
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-flash-latest")

    # --- Boot behaviour ---------------------------------------------------------------
    # Set to "false" when the database is loaded by other means (e.g. a one-time
    # migration from the local database) to avoid double-seeding.
    SEED_DB = os.environ.get("SEED_DB", "true").lower() == "true"
