"""Extended profile for patient accounts."""
from datetime import datetime
from utils.time import utcnow

from database.db import db


class Patient(db.Model):
    __tablename__ = "patients"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True,
        nullable=False,
    )

    full_name = db.Column(db.String(120), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    blood_group = db.Column(db.String(10), nullable=True)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    emergency_contact_name = db.Column(db.String(120), nullable=True)
    emergency_contact_phone = db.Column(db.String(20), nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    appointments = db.relationship(
        "Appointment", backref="patient", lazy="dynamic", cascade="all, delete-orphan"
    )
    medical_records = db.relationship(
        "MedicalHistory", backref="patient", lazy="dynamic", cascade="all, delete-orphan"
    )
    prescriptions = db.relationship(
        "Prescription", backref="patient", lazy="dynamic", cascade="all, delete-orphan"
    )
    predictions = db.relationship(
        "PredictionHistory", backref="patient", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Patient {self.full_name}>"

    @property
    def profile_complete(self) -> bool:
        return all([self.full_name, self.age, self.gender, self.phone])
