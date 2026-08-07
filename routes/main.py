"""Public routes: landing page and role-based post-login redirect."""
from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    return render_template("landing.html")


@main_bp.route("/dashboard")
def dashboard():
    """Redirect authenticated users to their role dashboard."""
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login"))
    if current_user.is_admin:
        return redirect(url_for("admin.dashboard"))
    if current_user.is_doctor:
        return redirect(url_for("doctor.dashboard"))
    return redirect(url_for("patient.dashboard"))
