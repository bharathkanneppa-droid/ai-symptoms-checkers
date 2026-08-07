"""Doctor dashboard: appointments, patients, prescriptions, availability."""
from datetime import datetime, date

from flask import (
    Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for,
)
from flask_login import current_user
from sqlalchemy import or_

from database.db import db
from models import (
    Appointment, DoctorAvailability, MedicalHistory, Notification,
    Patient, Prescription, PrescriptionItem, User,
)
from utils.decorators import doctor_required
from utils.helpers import add_patient_record, notify

doctor_bp = Blueprint("doctor", __name__, url_prefix="/doctor")

WEEKDAYS = [
    ("0", "Monday"), ("1", "Tuesday"), ("2", "Wednesday"), ("3", "Thursday"),
    ("4", "Friday"), ("5", "Saturday"), ("6", "Sunday"),
]


def _doctor_or_404():
    """Return the current user's Doctor row or 404."""
    doctor = current_user.doctor
    if not doctor:
        abort(404)
    return doctor


# --------------------------------------------------------------------------- #
# Dashboard
# --------------------------------------------------------------------------- #
@doctor_bp.route("/dashboard")
@doctor_required
def dashboard():
    doctor = _doctor_or_404()
    today = date.today()

    todays = (
        Appointment.query.filter_by(doctor_id=doctor.id, appointment_date=today)
        .order_by(Appointment.appointment_time)
        .all()
    )
    upcoming = (
        Appointment.query.filter(
            Appointment.doctor_id == doctor.id,
            Appointment.appointment_date > today,
            Appointment.status == Appointment.STATUS_ACCEPTED,
        )
        .order_by(Appointment.appointment_date)
        .limit(5)
        .all()
    )
    stats = {
        "today": len(todays),
        "pending": Appointment.query.filter_by(
            doctor_id=doctor.id, status=Appointment.STATUS_PENDING
        ).count(),
        "accepted": Appointment.query.filter_by(
            doctor_id=doctor.id, status=Appointment.STATUS_ACCEPTED
        ).count(),
        "completed": Appointment.query.filter_by(
            doctor_id=doctor.id, status=Appointment.STATUS_COMPLETED
        ).count(),
    }
    return render_template(
        "doctor/dashboard.html",
        doctor=doctor,
        todays=todays,
        upcoming=upcoming,
        stats=stats,
        today=today,
    )


# --------------------------------------------------------------------------- #
# Appointments
# --------------------------------------------------------------------------- #
@doctor_bp.route("/appointments")
@doctor_required
def appointments():
    doctor = _doctor_or_404()
    status = request.args.get("status", "")
    query = Appointment.query.filter_by(doctor_id=doctor.id)
    if status in {"pending", "accepted", "rejected", "completed", "cancelled"}:
        query = query.filter(Appointment.status == status)
    appointments_list = (
        query.order_by(Appointment.appointment_date.desc(), Appointment.appointment_time)
        .all()
    )
    return render_template(
        "doctor/appointments.html", appointments=appointments_list, active=status
    )


@doctor_bp.route("/appointments/<int:appointment_id>/<action>", methods=["POST"])
@doctor_required
def appointment_action(appointment_id, action):
    doctor = _doctor_or_404()
    appointment = Appointment.query.filter_by(
        id=appointment_id, doctor_id=doctor.id
    ).first_or_404()

    if action == "accept":
        appointment.status = Appointment.STATUS_ACCEPTED
        notify(
            appointment.patient.user_id,
            "Appointment accepted",
            f"Your appointment with {doctor.full_name} on "
            f"{appointment.appointment_date.strftime('%d %b %Y')} at "
            f"{appointment.appointment_time} has been accepted.",
            "appointment",
            url_for("appointments.my_appointments"),
        )
        flash("Appointment accepted.", "success")
    elif action == "reject":
        appointment.status = Appointment.STATUS_REJECTED
        notify(
            appointment.patient.user_id,
            "Appointment rejected",
            f"Your appointment with {doctor.full_name} on "
            f"{appointment.appointment_date.strftime('%d %b %Y')} was rejected.",
            "appointment",
            url_for("appointments.my_appointments"),
        )
        flash("Appointment rejected.", "info")
    elif action == "complete":
        appointment.status = Appointment.STATUS_COMPLETED
        notify(
            appointment.patient.user_id,
            "Appointment completed",
            f"Your appointment with {doctor.full_name} was marked complete.",
            "appointment",
            url_for("appointments.my_appointments"),
        )
        flash("Appointment marked as complete.", "success")
    else:
        abort(400)

    db.session.commit()
    return redirect(url_for("doctor.appointments"))


# --------------------------------------------------------------------------- #
# Patients
# --------------------------------------------------------------------------- #
@doctor_bp.route("/patients")
@doctor_required
def patients():
    query = request.args.get("q", "").strip()
    if query:
        pattern = f"%{query}%"
        patients_list = (
            Patient.query.join(User)
            .filter(
                or_(
                    Patient.full_name.ilike(pattern),
                    Patient.phone.ilike(pattern),
                    User.email.ilike(pattern),
                )
            )
            .order_by(Patient.full_name)
            .all()
        )
    else:
        patients_list = Patient.query.order_by(Patient.full_name).all()
    return render_template(
        "doctor/patients.html", patients=patients_list, query=query
    )


@doctor_bp.route("/patients/<int:patient_id>")
@doctor_required
def patient_detail(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    records = (
        MedicalHistory.query.filter_by(patient_id=patient.id)
        .order_by(MedicalHistory.created_at.desc())
        .all()
    )
    prescriptions = (
        Prescription.query.filter_by(patient_id=patient.id)
        .order_by(Prescription.created_at.desc())
        .all()
    )
    appointments = (
        Appointment.query.filter_by(patient_id=patient.id)
        .order_by(Appointment.appointment_date.desc())
        .limit(10)
        .all()
    )
    return render_template(
        "doctor/patient_detail.html",
        patient=patient,
        records=records,
        prescriptions=prescriptions,
        appointments=appointments,
    )


# --------------------------------------------------------------------------- #
# Prescriptions
# --------------------------------------------------------------------------- #
@doctor_bp.route("/prescriptions/new", methods=["GET", "POST"])
@doctor_required
def new_prescription():
    doctor = _doctor_or_404()
    patient_id = request.args.get("patient_id", type=int) or request.form.get("patient_id", type=int)

    if request.method == "POST":
        patient_id = request.form.get("patient_id", type=int)
        patient = Patient.query.get(patient_id)
        if not patient:
            flash("Please choose a valid patient.", "danger")
            return redirect(url_for("doctor.new_prescription"))

        diagnosis = request.form.get("diagnosis", "").strip()
        notes = request.form.get("notes", "").strip()
        follow_up = request.form.get("follow_up_in_days", type=int)

        if not diagnosis:
            flash("Diagnosis is required.", "danger")
        else:
            prescription = Prescription(
                patient_id=patient.id,
                doctor_id=doctor.id,
                diagnosis=diagnosis,
                notes=notes or None,
                follow_up_in_days=follow_up,
            )
            db.session.add(prescription)
            db.session.flush()

            medicine_names = request.form.getlist("medicine_name")
            dosages = request.form.getlist("dosage")
            frequencies = request.form.getlist("frequency")
            durations = request.form.getlist("duration")
            instructions = request.form.getlist("instructions")

            for i, medicine in enumerate(medicine_names):
                medicine = (medicine or "").strip()
                if not medicine:
                    continue
                db.session.add(
                    PrescriptionItem(
                        prescription_id=prescription.id,
                        medicine_name=medicine,
                        dosage=(dosages[i].strip() if i < len(dosages) else ""),
                        frequency=(frequencies[i].strip() if i < len(frequencies) else ""),
                        duration=(durations[i].strip() if i < len(durations) else ""),
                        instructions=(instructions[i].strip() if i < len(instructions) else ""),
                    )
                )

            # Log the encounter to the patient's medical history.
            add_patient_record(
                patient_id=patient.id,
                doctor_id=doctor.id,
                diagnosis=diagnosis,
                treatment=notes,
            )
            notify(
                patient.user_id,
                "New prescription",
                f"Dr. {doctor.full_name} uploaded a prescription for you.",
                "prescription",
                url_for("prescriptions.detail", prescription_id=prescription.id),
            )
            db.session.commit()
            flash(f"Prescription created for {patient.full_name}.", "success")
            return redirect(url_for("doctor.my_prescriptions"))

    return render_template(
        "doctor/prescription_form.html",
        patient_id=patient_id,
        patients=Patient.query.order_by(Patient.full_name).all(),
    )


@doctor_bp.route("/prescriptions")
@doctor_required
def my_prescriptions():
    doctor = _doctor_or_404()
    prescriptions = (
        Prescription.query.filter_by(doctor_id=doctor.id)
        .order_by(Prescription.created_at.desc())
        .all()
    )
    return render_template("doctor/my_prescriptions.html", prescriptions=prescriptions)


# --------------------------------------------------------------------------- #
# Availability
# --------------------------------------------------------------------------- #
@doctor_bp.route("/availability", methods=["GET", "POST"])
@doctor_required
def availability():
    doctor = _doctor_or_404()

    if request.method == "POST":
        # Toggle the doctor's overall availability.
        if "toggle_global" in request.form:
            doctor.is_available = not doctor.is_available
            db.session.commit()
            flash("Availability updated.", "success")
            return redirect(url_for("doctor.availability"))

        # Update the weekly schedule.
        days = request.form.getlist("days")
        starts = request.form.getlist("start_time")
        ends = request.form.getlist("end_time")
        for day in WEEKDAYS:
            day_id = day[0]
            entry = DoctorAvailability.query.filter_by(
                doctor_id=doctor.id, day_of_week=int(day_id)
            ).first()
            if day_id in days:
                idx = days.index(day_id)
                if entry is None:
                    entry = DoctorAvailability(doctor_id=doctor.id, day_of_week=int(day_id))
                    db.session.add(entry)
                entry.is_available = True
                entry.start_time = starts[idx] if idx < len(starts) else "09:00"
                entry.end_time = ends[idx] if idx < len(ends) else "17:00"
            else:
                if entry is None:
                    entry = DoctorAvailability(doctor_id=doctor.id, day_of_week=int(day_id))
                    db.session.add(entry)
                entry.is_available = False
        db.session.commit()
        flash("Weekly schedule saved.", "success")
        return redirect(url_for("doctor.availability"))

    schedule = {entry.day_of_week: entry for entry in doctor.availabilities}
    return render_template(
        "doctor/availability.html", schedule=schedule, weekdays=WEEKDAYS, doctor=doctor
    )
