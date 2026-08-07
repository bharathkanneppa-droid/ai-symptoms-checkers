"""Admin panel: doctors, patients, appointments, departments, analytics."""
from datetime import date, datetime, timedelta

from flask import (
    Blueprint, abort, flash, redirect, render_template, request, url_for,
)
from sqlalchemy import func

from database.db import db
from models import (
    Appointment, Department, Doctor, Notification, Patient, User,
)
from utils.decorators import admin_required
from utils.helpers import notify

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


# --------------------------------------------------------------------------- #
# Dashboard / analytics
# --------------------------------------------------------------------------- #
@admin_bp.route("/dashboard")
@admin_required
def dashboard():
    today = date.today()
    week_ago = today - timedelta(days=6)

    patients = Patient.query.count()
    doctors = Doctor.query.count()
    appointments = Appointment.query.count()
    pending = Appointment.query.filter_by(status=Appointment.STATUS_PENDING).count()

    # Appointments per day for the last 7 days (for the line chart).
    days, counts = [], []
    for offset in range(6, -1, -1):
        day = today - timedelta(days=offset)
        days.append(day.strftime("%d %b"))
        counts.append(
            Appointment.query.filter(
                Appointment.created_at >= datetime.combine(day, datetime.min.time()),
                Appointment.created_at < datetime.combine(
                    day + timedelta(days=1), datetime.min.time()
                ),
            ).count()
        )

    # Appointments per department (for the bar chart).
    dept_rows = (
        db.session.query(Department.name, func.count(Appointment.id))
        .outerjoin(Doctor, Doctor.department_id == Department.id)
        .outerjoin(Appointment, Appointment.doctor_id == Doctor.id)
        .group_by(Department.name)
        .all()
    )
    dept_names = [r[0] for r in dept_rows]
    dept_counts = [r[1] for r in dept_rows]

    status_counts = {
        s: Appointment.query.filter_by(status=s).count()
        for s in (
            Appointment.STATUS_PENDING,
            Appointment.STATUS_ACCEPTED,
            Appointment.STATUS_REJECTED,
            Appointment.STATUS_COMPLETED,
            Appointment.STATUS_CANCELLED,
        )
    }

    recent = (
        Appointment.query.order_by(Appointment.created_at.desc()).limit(8).all()
    )
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(6).all()

    return render_template(
        "admin/dashboard.html",
        stats={"patients": patients, "doctors": doctors,
               "appointments": appointments, "pending": pending},
        days=days, counts=counts,
        dept_names=dept_names, dept_counts=dept_counts,
        status_counts=status_counts,
        recent=recent, recent_patients=recent_patients,
    )


# --------------------------------------------------------------------------- #
# Doctors
# --------------------------------------------------------------------------- #
@admin_bp.route("/doctors")
@admin_required
def doctors():
    return render_template(
        "admin/doctors.html", doctors=Doctor.query.order_by(Doctor.full_name).all()
    )


@admin_bp.route("/doctors/add", methods=["GET", "POST"])
@admin_required
def add_doctor():
    if request.method == "POST":
        from app import bcrypt

        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        full_name = request.form.get("full_name", "").strip()
        specialization = request.form.get("specialization", "").strip()
        department_id = request.form.get("department_id", type=int)
        qualification = request.form.get("qualification", "").strip()
        experience_years = request.form.get("experience_years", type=int)
        license_number = request.form.get("license_number", "").strip()
        phone = request.form.get("phone", "").strip()
        fee = request.form.get("fee", type=float)

        errors = []
        if not all([username, email, password, full_name]):
            errors.append("Username, email, password and full name are required.")
        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if User.query.filter_by(email=email).first():
            errors.append("A user with that email already exists.")
        if not Department.query.get(department_id or 0):
            errors.append("Please choose a valid department.")

        if errors:
            for error in errors:
                flash(error, "danger")
        else:
            user = User(
                username=username,
                email=email,
                password_hash=bcrypt.generate_password_hash(password).decode("utf-8"),
                role=User.ROLE_DOCTOR,
                is_active_flag=True,
                is_email_verified=True,
            )
            db.session.add(user)
            db.session.flush()
            db.session.add(
                Doctor(
                    user_id=user.id,
                    department_id=department_id,
                    full_name=full_name,
                    specialization=specialization or None,
                    qualification=qualification or None,
                    experience_years=experience_years,
                    license_number=license_number or None,
                    phone=phone or None,
                    fee=fee,
                    is_available=True,
                )
            )
            db.session.commit()
            flash(f"Doctor {full_name} added successfully!", "success")
            return redirect(url_for("admin.doctors"))

    departments = Department.query.order_by(Department.name).all()
    return render_template("admin/add_doctor.html", departments=departments)


@admin_bp.route("/doctors/<int:doctor_id>/delete", methods=["POST"])
@admin_required
def delete_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    name = doctor.full_name
    if doctor.appointments.count():
        flash("Cannot delete: this doctor has appointments. Cancel them first.", "danger")
    else:
        db.session.delete(doctor)
        if doctor.user:
            db.session.delete(doctor.user)
        db.session.commit()
        flash(f"Doctor {name} removed.", "info")
    return redirect(url_for("admin.doctors"))


@admin_bp.route("/doctors/<int:doctor_id>/toggle", methods=["POST"])
@admin_required
def toggle_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_available = not doctor.is_available
    db.session.commit()
    flash(f"{doctor.full_name} is now {'available' if doctor.is_available else 'unavailable'}.",
          "info")
    return redirect(url_for("admin.doctors"))


# --------------------------------------------------------------------------- #
# Patients
# --------------------------------------------------------------------------- #
@admin_bp.route("/patients")
@admin_required
def patients():
    query = request.args.get("q", "").strip()
    if query:
        pattern = f"%{query}%"
        patients_list = (
            Patient.query.join(User)
            .filter(
                (Patient.full_name.ilike(pattern)) | (User.email.ilike(pattern))
            )
            .order_by(Patient.full_name)
            .all()
        )
    else:
        patients_list = Patient.query.order_by(Patient.full_name).all()
    return render_template("admin/patients.html", patients=patients_list, query=query)


@admin_bp.route("/patients/<int:patient_id>/toggle", methods=["POST"])
@admin_required
def toggle_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    user = patient.user
    user.is_active_flag = not user.is_active_flag
    db.session.commit()
    flash(f"{patient.full_name} {'deactivated' if not user.is_active_flag else 'activated'}.",
          "info")
    return redirect(url_for("admin.patients"))


# --------------------------------------------------------------------------- #
# Appointments
# --------------------------------------------------------------------------- #
@admin_bp.route("/appointments")
@admin_required
def appointments():
    status = request.args.get("status", "")
    query = Appointment.query
    if status in {"pending", "accepted", "rejected", "completed", "cancelled"}:
        query = query.filter(Appointment.status == status)
    appointments_list = (
        query.order_by(Appointment.created_at.desc()).limit(200).all()
    )
    return render_template(
        "admin/appointments.html", appointments=appointments_list, active=status
    )


@admin_bp.route("/appointments/<int:appointment_id>/cancel", methods=["POST"])
@admin_required
def cancel_appointment(appointment_id):
    appointment = Appointment.query.get_or_404(appointment_id)
    if appointment.status not in (
        Appointment.STATUS_PENDING, Appointment.STATUS_ACCEPTED
    ):
        flash("This appointment can no longer be cancelled.", "warning")
    else:
        appointment.status = Appointment.STATUS_CANCELLED
        notify(
            appointment.patient.user_id,
            "Appointment cancelled",
            f"Your appointment with {appointment.doctor.full_name} was cancelled by the admin.",
            "appointment",
        )
        notify(
            appointment.doctor.user_id,
            "Appointment cancelled",
            f"Appointment with {appointment.patient.full_name} was cancelled by the admin.",
            "appointment",
        )
        db.session.commit()
        flash("Appointment cancelled.", "info")
    return redirect(url_for("admin.appointments"))


# --------------------------------------------------------------------------- #
# Departments
# --------------------------------------------------------------------------- #
@admin_bp.route("/departments", methods=["GET", "POST"])
@admin_required
def departments():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "").strip()
        icon = request.form.get("icon", "bi-activity").strip()
        if not name:
            flash("Department name is required.", "danger")
        elif Department.query.filter_by(name=name).first():
            flash("That department already exists.", "danger")
        else:
            db.session.add(Department(name=name, description=description or None, icon=icon or None))
            db.session.commit()
            flash(f"Department '{name}' added.", "success")
            return redirect(url_for("admin.departments"))

    departments_list = Department.query.order_by(Department.name).all()
    return render_template(
        "admin/departments.html", departments=departments_list
    )


@admin_bp.route("/departments/<int:department_id>/edit", methods=["POST"])
@admin_required
def edit_department(department_id):
    department = Department.query.get_or_404(department_id)
    name = request.form.get("name", "").strip()
    if not name:
        flash("Department name is required.", "danger")
    else:
        department.name = name
        department.description = request.form.get("description", "").strip() or None
        department.icon = request.form.get("icon", "bi-activity").strip() or None
        db.session.commit()
        flash("Department updated.", "success")
    return redirect(url_for("admin.departments"))


@admin_bp.route("/departments/<int:department_id>/delete", methods=["POST"])
@admin_required
def delete_department(department_id):
    department = Department.query.get_or_404(department_id)
    if department.doctors.count():
        flash("Cannot delete: doctors are assigned to this department.", "danger")
    else:
        db.session.delete(department)
        db.session.commit()
        flash(f"Department '{department.name}' deleted.", "info")
    return redirect(url_for("admin.departments"))
