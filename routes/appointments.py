"""Appointment booking and management."""
from datetime import datetime, timedelta
from utils.time import utcnow

from flask import (
    Blueprint, flash, jsonify, redirect, render_template, request, url_for,
)
from flask_login import current_user
from sqlalchemy import or_

from appointments.slots import generate_slots
from database.db import db
from models import (
    Appointment, Department, Doctor, Notification, Patient,
)
from utils.decorators import patient_required
from utils.helpers import notify

appointments_bp = Blueprint("appointments", __name__, url_prefix="/appointments")


def _parse_date(value):
    return datetime.strptime(value, "%Y-%m-%d").date() if value else None


# --------------------------------------------------------------------------- #
# Patient booking flow: Department -> Doctor -> Date -> Time -> Confirm
# --------------------------------------------------------------------------- #
@appointments_bp.route("/book", methods=["GET", "POST"])
@patient_required
def book():
    if request.method == "POST":
        department_id = request.form.get("department_id")
        doctor_id = request.form.get("doctor_id")
        date_value = request.form.get("appointment_date")
        time_value = request.form.get("appointment_time")
        reason = request.form.get("reason", "").strip()

        doctor = Doctor.query.get(doctor_id) if doctor_id else None
        appointment_date = _parse_date(date_value)
        errors = []

        if not doctor or not doctor.is_available:
            errors.append("Please select an available doctor.")
        if not appointment_date or appointment_date < utcnow().date():
            errors.append("Please pick a valid future date.")
        if not time_value:
            errors.append("Please select a time slot.")

        existing = None
        if doctor and appointment_date and time_value:
            existing = Appointment.query.filter_by(
                doctor_id=doctor.id,
                appointment_date=appointment_date,
                appointment_time=time_value,
            ).filter(
                Appointment.status.in_(
                    [Appointment.STATUS_PENDING, Appointment.STATUS_ACCEPTED]
                )
            ).first()

        if existing:
            errors.append("That slot is already booked - please choose another.")

        if not errors:
            appointment = Appointment(
                patient_id=current_user.patient.id,
                doctor_id=doctor.id,
                department_id=doctor.department_id,
                appointment_date=appointment_date,
                appointment_time=time_value,
                status=Appointment.STATUS_PENDING,
                reason=reason,
            )
            db.session.add(appointment)
            notify(
                doctor.user_id,
                "New appointment request",
                f"{current_user.patient.full_name} booked {time_value} on "
                f"{appointment_date.strftime('%d %b %Y')}.",
                "appointment",
                url_for("doctor.appointments"),
            )
            db.session.commit()
            flash("Appointment booked successfully! Waiting for doctor confirmation.", "success")
            return redirect(url_for("appointments.my_appointments"))

        for error in errors:
            flash(error, "danger")

    departments = Department.query.order_by(Department.name).all()
    return render_template("patient/book_appointment.html", departments=departments)


@appointments_bp.route("/api/doctors", methods=["GET"])
@patient_required
def api_doctors_by_department():
    department_id = request.args.get("department_id", type=int)
    doctors = (
        Doctor.query.filter_by(department_id=department_id, is_available=True)
        .order_by(Doctor.full_name)
        .all()
    )
    return jsonify([
        {"id": d.id, "name": d.full_name, "specialization": d.specialization or "General",
         "fee": float(d.fee) if d.fee else None, "experience_years": d.experience_years}
        for d in doctors
    ])


@appointments_bp.route("/api/slots", methods=["GET"])
@patient_required
def api_slots():
    doctor_id = request.args.get("doctor_id", type=int)
    date_value = request.args.get("date")
    doctor = Doctor.query.get(doctor_id)
    appointment_date = _parse_date(date_value)
    if not doctor or not appointment_date:
        return jsonify({"error": "Invalid doctor or date."}), 400

    booked = [
        a.appointment_time for a in Appointment.query.filter_by(
            doctor_id=doctor.id, appointment_date=appointment_date
        ).filter(
            Appointment.status.in_(
                [Appointment.STATUS_PENDING, Appointment.STATUS_ACCEPTED]
            )
        ).all()
    ]
    slots = generate_slots(doctor, appointment_date, booked)
    return jsonify({"slots": slots})


# --------------------------------------------------------------------------- #
# Patient's own appointments
# --------------------------------------------------------------------------- #
@appointments_bp.route("/my")
@patient_required
def my_appointments():
    status = request.args.get("status", "")
    query = Appointment.query.filter_by(patient_id=current_user.patient.id)
    if status in {s for s in ("pending", "accepted", "rejected", "completed", "cancelled")}:
        query = query.filter(Appointment.status == status)
    appointments = (
        query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time.desc())
        .all()
    )
    return render_template(
        "patient/appointments.html", appointments=appointments, active=status
    )


@appointments_bp.route("/<int:appointment_id>/cancel", methods=["POST"])
@patient_required
def cancel(appointment_id):
    appointment = Appointment.query.filter_by(
        id=appointment_id, patient_id=current_user.patient.id
    ).first_or_404()
    if appointment.status not in (Appointment.STATUS_PENDING, Appointment.STATUS_ACCEPTED):
        flash("This appointment can no longer be cancelled.", "warning")
    else:
        appointment.status = Appointment.STATUS_CANCELLED
        notify(
            appointment.doctor.user_id,
            "Appointment cancelled",
            f"{current_user.patient.full_name} cancelled their {appointment.appointment_time} "
            f"appointment on {appointment.appointment_date.strftime('%d %b %Y')}.",
            "appointment",
        )
        db.session.commit()
        flash("Appointment cancelled.", "info")
    return redirect(url_for("appointments.my_appointments"))
