"""Patient dashboard, profile, settings and history."""
from datetime import datetime
from utils.time import utcnow

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user
from sqlalchemy import or_

from database.db import db
from models import Appointment, MedicalHistory, Notification, Prescription
from utils.decorators import patient_required

patient_bp = Blueprint("patient", __name__, url_prefix="/patient")

VALID_GENDERS = {"male", "female", "other", ""}
VALID_BLOOD = {
    "A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-", "",
}


@patient_bp.route("/dashboard")
@patient_required
def dashboard():
    patient = current_user.patient
    now = utcnow()

    upcoming = (
        Appointment.query.filter(
            Appointment.patient_id == patient.id,
            Appointment.status == Appointment.STATUS_ACCEPTED,
            Appointment.appointment_date >= now.date(),
        )
        .order_by(Appointment.appointment_date, Appointment.appointment_time)
        .all()
    )
    pending = Appointment.query.filter_by(
        patient_id=patient.id, status=Appointment.STATUS_PENDING
    ).count()
    completed = Appointment.query.filter_by(
        patient_id=patient.id, status=Appointment.STATUS_COMPLETED
    ).count()
    prescriptions = Prescription.query.filter_by(patient_id=patient.id).count()
    unread = Notification.query.filter_by(
        user_id=current_user.id, is_read=False
    ).count()

    recent_appointments = (
        Appointment.query.filter_by(patient_id=patient.id)
        .order_by(Appointment.created_at.desc())
        .limit(5)
        .all()
    )
    recent_prescriptions = (
        Prescription.query.filter_by(patient_id=patient.id)
        .order_by(Prescription.created_at.desc())
        .limit(5)
        .all()
    )

    return render_template(
        "patient/dashboard.html",
        patient=patient,
        upcoming=upcoming,
        pending=pending,
        completed=completed,
        prescriptions_count=prescriptions,
        unread=unread,
        recent_appointments=recent_appointments,
        recent_prescriptions=recent_prescriptions,
    )


@patient_bp.route("/history")
@patient_required
def history():
    from models import PredictionHistory

    patient = current_user.patient
    medical_records = (
        MedicalHistory.query.filter_by(patient_id=patient.id)
        .order_by(MedicalHistory.created_at.desc())
        .all()
    )
    predictions = (
        PredictionHistory.query.filter_by(patient_id=patient.id)
        .order_by(PredictionHistory.created_at.desc())
        .all()
    )
    return render_template(
        "patient/medical_history.html",
        medical_records=medical_records,
        predictions=predictions,
    )


@patient_bp.route("/profile", methods=["GET", "POST"])
@patient_required
def profile():
    patient = current_user.patient
    if request.method == "POST":
        full_name = request.form.get("full_name", "").strip()
        age = request.form.get("age", "").strip()
        gender = (request.form.get("gender") or "").strip().lower()
        blood_group = (request.form.get("blood_group") or "").strip().upper()
        address = request.form.get("address", "").strip()
        phone = request.form.get("phone", "").strip()
        emergency_name = request.form.get("emergency_contact_name", "").strip()
        emergency_phone = request.form.get("emergency_contact_phone", "").strip()

        if not full_name:
            flash("Full name is required.", "danger")
        elif age and not age.isdigit():
            flash("Age must be a number.", "danger")
        elif gender not in VALID_GENDERS:
            flash("Please choose a valid gender.", "danger")
        elif blood_group not in VALID_BLOOD:
            flash("Please choose a valid blood group.", "danger")
        else:
            patient.full_name = full_name
            patient.age = int(age) if age else None
            patient.gender = gender.capitalize() if gender else None
            patient.blood_group = blood_group if blood_group else None
            patient.address = address or None
            patient.phone = phone or None
            patient.emergency_contact_name = emergency_name or None
            patient.emergency_contact_phone = emergency_phone or None
            db.session.commit()
            flash("Profile updated successfully!", "success")
            return redirect(url_for("patient.profile"))

    return render_template("patient/profile.html", patient=patient)


@patient_bp.route("/settings", methods=["GET", "POST"])
@patient_required
def settings():
    if request.method == "POST":
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm = request.form.get("confirm_password", "")

        from app import bcrypt

        if not bcrypt.check_password_hash(current_user.password_hash, current_password):
            flash("Current password is incorrect.", "danger")
        elif len(new_password) < 8:
            flash("New password must be at least 8 characters.", "danger")
        elif new_password != confirm:
            flash("New passwords do not match.", "danger")
        else:
            current_user.password_hash = bcrypt.generate_password_hash(new_password).decode("utf-8")
            db.session.commit()
            flash("Password changed successfully!", "success")
            return redirect(url_for("patient.settings"))

    return render_template("patient/settings.html")
