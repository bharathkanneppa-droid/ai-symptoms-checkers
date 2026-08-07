"""Seed the database with the data the app needs to be useful on first run.

* A default admin account (admin@medassist.local / admin123 - change in prod).
* All departments.
* A handful of demo doctors across departments.
* Demo patient + a few appointments/prescriptions to make the dashboards look
  alive on first launch.
"""
import logging
from datetime import date, timedelta

from database.db import db
from flask_bcrypt import Bcrypt

logger = logging.getLogger(__name__)

DEFAULT_ADMIN = {
    "username": "admin",
    "email": "admin@medassist.local",
    "password": "admin123",
}

DEPARTMENTS = [
    ("General Medicine", "Everyday health concerns and check-ups.", "bi-activity"),
    ("Cardiology", "Heart and blood vessel conditions.", "bi-heart-pulse"),
    ("Neurology", "Brain, spine and nervous system disorders.", "bi-braces-asterisk"),
    ("ENT", "Ear, nose and throat conditions.", "bi-ear"),
    ("Dermatology", "Skin, hair and nail conditions.", "bi-shield-plus"),
    ("Gynecology", "Women's health and reproductive care.", "bi-heart"),
    ("Pediatrics", "Health care for infants and children.", "bi-emoji-smile"),
    ("Orthopedics", "Bones, joints and muscle conditions.", "bi-person-arms-up"),
    ("Ophthalmology", "Eye health and vision care.", "bi-eye"),
    ("Pulmonology", "Lungs and respiratory conditions.", "bi-wind"),
    ("Gastroenterology", "Digestive system conditions.", "bi-egg-fried"),
    ("Urology", "Urinary tract and kidney conditions.", "bi-droplet"),
    ("Psychiatry", "Mental health and emotional well-being.", "bi-brain"),
]

# name, specialization, department, qualification, experience, license, email
DEMO_DOCTORS = [
    ("Dr. Arjun Mehta", "General Physician", "General Medicine", "MBBS, MD (Internal Medicine)", 12, "LIC-1001", "arjun@medassist.local"),
    ("Dr. Priya Sharma", "Cardiologist", "Cardiology", "MBBS, DM (Cardiology)", 15, "LIC-1002", "priya@medassist.local"),
    ("Dr. Ravi Nair", "Neurologist", "Neurology", "MBBS, DM (Neurology)", 10, "LIC-1003", "ravi@medassist.local"),
    ("Dr. Sneha Kulkarni", "ENT Specialist", "ENT", "MBBS, MS (ENT)", 8, "LIC-1004", "sneha@medassist.local"),
    ("Dr. Vikram Rao", "Dermatologist", "Dermatology", "MBBS, MD (Dermatology)", 9, "LIC-1005", "vikram@medassist.local"),
    ("Dr. Meera Iyer", "Gynecologist", "Gynecology", "MBBS, MS (OBG)", 11, "LIC-1006", "meera@medassist.local"),
]


def seed_if_empty():
    """Create tables and seed baseline data. Safe to call on every boot."""
    db.create_all()

    # --- Admin ---------------------------------------------------------
    from models import User

    if not User.query.filter_by(role=User.ROLE_ADMIN).first():
        bcrypt = Bcrypt()
        admin = User(
            username=DEFAULT_ADMIN["username"],
            email=DEFAULT_ADMIN["email"],
            password_hash=bcrypt.generate_password_hash(DEFAULT_ADMIN["password"]).decode("utf-8"),
            role=User.ROLE_ADMIN,
            is_active_flag=True,
            is_email_verified=True,
        )
        db.session.add(admin)
        logger.info("Created default admin: %s / %s", DEFAULT_ADMIN["email"], DEFAULT_ADMIN["password"])

    # --- Departments -----------------------------------------------------
    from models import Department

    dept_by_name = {}
    if Department.query.count() == 0:
        for name, desc, icon in DEPARTMENTS:
            dept = Department(name=name, description=desc, icon=icon)
            db.session.add(dept)
            dept_by_name[name] = dept
        logger.info("Seeded %d departments", len(DEPARTMENTS))
    else:
        dept_by_name = {d.name: d for d in Department.query.all()}

    db.session.flush()

    # --- Demo doctors ------------------------------------------------------
    from models import Doctor

    if Doctor.query.count() == 0:
        bcrypt = Bcrypt()
        for name, spec, dept_name, qual, exp, lic, email in DEMO_DOCTORS:
            user = User(
                username=email.split("@")[0],
                email=email,
                password_hash=bcrypt.generate_password_hash("doctor123").decode("utf-8"),
                role=User.ROLE_DOCTOR,
                is_active_flag=True,
                is_email_verified=True,
            )
            db.session.add(user)
            db.session.flush()
            doctor = Doctor(
                user_id=user.id,
                department_id=dept_by_name.get(dept_name).id if dept_name in dept_by_name else None,
                full_name=name,
                specialization=spec,
                qualification=qual,
                experience_years=exp,
                license_number=lic,
                phone="+91 90000 00000",
                bio=f"{spec} with {exp} years of experience.",
                is_available=True,
            )
            db.session.add(doctor)
        logger.info("Seeded %d demo doctors (password: doctor123)", len(DEMO_DOCTORS))

    # --- Demo patient + activity --------------------------------------------
    from models import Patient

    if Patient.query.count() == 0:
        bcrypt = Bcrypt()
        patient_user = User(
            username="demo_patient",
            email="patient@medassist.local",
            password_hash=bcrypt.generate_password_hash("patient123").decode("utf-8"),
            role=User.ROLE_PATIENT,
            is_active_flag=True,
            is_email_verified=True,
        )
        db.session.add(patient_user)
        db.session.flush()
        patient = Patient(
            user_id=patient_user.id,
            full_name="Demo Patient",
            age=28,
            gender="Male",
            blood_group="O+",
            phone="+91 91234 56780",
            address="123 Demo Street, Your City",
            emergency_contact_name="Jane Doe",
            emergency_contact_phone="+91 99999 00000",
        )
        db.session.add(patient)
        db.session.flush()

        from models import Appointment, MedicalHistory

        doctor = Doctor.query.first()
        appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            department_id=doctor.department_id,
            appointment_date=date.today() + timedelta(days=2),
            appointment_time="10:00",
            status=Appointment.STATUS_ACCEPTED,
            reason="Follow-up for fever and cold",
        )
        db.session.add(appointment)
        db.session.add(
            MedicalHistory(
                patient_id=patient.id,
                doctor_id=doctor.id,
                diagnosis="Common Cold",
                symptoms="fever, runny nose, sore throat",
                treatment="Paracetamol 500mg twice daily for 3 days",
                notes="Hydration and rest advised.",
            )
        )
        logger.info("Seeded demo patient (password: patient123)")

    db.session.commit()
