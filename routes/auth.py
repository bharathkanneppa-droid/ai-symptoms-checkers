"""Authentication: register, login, logout, verification and password reset."""
import secrets
from datetime import datetime, timedelta
from utils.time import utcnow

from flask import (
    Blueprint, flash, redirect, render_template, request, url_for,
)
from flask_login import current_user, login_user, logout_user
from sqlalchemy.exc import IntegrityError

from config import Config
from database.db import db
from models import Patient, User
from utils.email import send_password_reset_email, send_verification_email

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

MIN_PASSWORD_LEN = 8


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def _validate_password(password):
    if len(password) < MIN_PASSWORD_LEN:
        return f"Password must be at least {MIN_PASSWORD_LEN} characters long."
    return None


# --------------------------------------------------------------------------- #
# Register
# --------------------------------------------------------------------------- #
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
        elif "@" not in email:
            flash("Please enter a valid email address.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            error = _validate_password(password)
            if error:
                flash(error, "danger")
            elif User.query.filter_by(email=email).first():
                flash("An account with that email already exists.", "danger")
            else:
                from app import bcrypt
                user = User(
                    username=username,
                    email=email,
                    password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
                    role=User.ROLE_PATIENT,
                    is_email_verified=not Config.EMAIL_VERIFICATION_REQUIRED,
                )
                if Config.EMAIL_VERIFICATION_REQUIRED:
                    user.verification_token = secrets.token_urlsafe(32)
                db.session.add(user)
                db.session.flush()  # assign user.id
                db.session.add(Patient(user_id=user.id, full_name=username))
                try:
                    db.session.commit()
                except IntegrityError:
                    db.session.rollback()
                    flash("That username or email is already in use.", "danger")
                    return render_template("auth/register.html")

                if user.verification_token:
                    send_verification_email(user, user.verification_token)
                    flash(
                        "Account created! A verification link has been sent to your email.",
                        "success",
                    )
                else:
                    flash("Account created! You can log in now.", "success")
                return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


# --------------------------------------------------------------------------- #
# Email verification (placeholder flow - emails are logged to console)
# --------------------------------------------------------------------------- #
@auth_bp.route("/verify-email/<token>")
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if not user:
        flash("Verification link is invalid or has expired.", "danger")
        return redirect(url_for("auth.login"))
    user.is_email_verified = True
    user.verification_token = None
    db.session.commit()
    flash("Email verified successfully! You can log in.", "success")
    return redirect(url_for("auth.login"))


# --------------------------------------------------------------------------- #
# Login
# --------------------------------------------------------------------------- #
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(email=email).first()
        if user and user.password_hash and bcrypt_check(user.password_hash, password):
            if not user.is_active_flag:
                flash("Your account has been disabled. Contact the administrator.", "danger")
            elif Config.EMAIL_VERIFICATION_REQUIRED and not user.is_email_verified:
                flash("Please verify your email address before logging in.", "warning")
            else:
                user.last_login_at = utcnow()
                db.session.commit()
                login_user(user, remember=remember)
                flash(
                    f"Thanks for logging in, {user.display_name}! "
                    f"You're signed in with {user.email}.",
                    "success",
                )
                return redirect(url_for("main.dashboard"))
        else:
            flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


def bcrypt_check(hashed, password):
    from app import bcrypt
    return bcrypt.check_password_hash(hashed, password)


# --------------------------------------------------------------------------- #
# Logout
# --------------------------------------------------------------------------- #
@auth_bp.route("/logout")
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# --------------------------------------------------------------------------- #
# Forgot password
# --------------------------------------------------------------------------- #
@auth_bp.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            user.reset_token_expires = utcnow() + timedelta(hours=1)
            db.session.commit()
            send_password_reset_email(user, token)
            # Placeholder: also print the link to the server console.
            print(f"\n[FORGOT PASSWORD] Reset link: {request.host_url}auth/reset-password/{token}\n")
        flash(
            "If that email exists, a password reset link has been sent.",
            "info",
        )
        return redirect(url_for("auth.login"))
    return render_template("auth/forgot_password.html")


# --------------------------------------------------------------------------- #
# Reset password
# --------------------------------------------------------------------------- #
@auth_bp.route("/reset-password/<token>", methods=["GET", "POST"])
def reset_password(token):
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < utcnow():
        flash("Reset link is invalid or has expired. Please request a new one.", "danger")
        return redirect(url_for("auth.forgot_password"))

    if request.method == "POST":
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")
        if password != confirm:
            flash("Passwords do not match.", "danger")
        else:
            error = _validate_password(password)
            if error:
                flash(error, "danger")
            else:
                from app import bcrypt
                user.password_hash = bcrypt.generate_password_hash(password).decode("utf-8")
                user.reset_token = None
                user.reset_token_expires = None
                db.session.commit()
                flash("Password updated! You can log in now.", "success")
                return redirect(url_for("auth.login"))

    return render_template("auth/reset_password.html", token=token)
