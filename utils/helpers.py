"""Small shared helpers used across blueprints."""
import re

from database.db import db
from models import Notification


def slugify(text):
    text = text.lower().strip()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def get_patient(user):
    return user.patient if user else None


def get_doctor(user):
    return user.doctor if user else None


def notify(user_id, title, message, type_="info", link=None):
    """Create an in-app notification for a user."""
    db.session.add(
        Notification(user_id=user_id, title=title, message=message, type=type_, link=link)
    )


def add_patient_record(patient_id, doctor_id, diagnosis, symptoms=None,
                       treatment=None, notes=None):
    """Append a row to the patient's medical history."""
    from models import MedicalHistory

    db.session.add(
        MedicalHistory(
            patient_id=patient_id,
            doctor_id=doctor_id,
            diagnosis=diagnosis,
            symptoms=symptoms,
            treatment=treatment,
            notes=notes,
        )
    )
