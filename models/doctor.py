"""Extended profile for doctor accounts."""
from datetime import datetime
from utils.time import utcnow

from database.db import db


class Doctor(db.Model):
    __tablename__ = "doctors"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True,
        nullable=False,
    )
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )

    full_name = db.Column(db.String(120), nullable=False)
    specialization = db.Column(db.String(120), nullable=True)
    qualification = db.Column(db.String(200), nullable=True)
    experience_years = db.Column(db.Integer, nullable=True)
    license_number = db.Column(db.String(60), nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    fee = db.Column(db.Numeric(10, 2), nullable=True, default=500)
    rating = db.Column(db.Numeric(3, 2), nullable=True, default=4.5)
    is_available = db.Column(db.Boolean, default=True, nullable=False)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    appointments = db.relationship(
        "Appointment", backref="doctor", lazy="dynamic", cascade="all, delete-orphan"
    )
    availabilities = db.relationship(
        "DoctorAvailability", backref="doctor", lazy="dynamic", cascade="all, delete-orphan"
    )
    prescriptions = db.relationship(
        "Prescription", backref="doctor", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Doctor {self.full_name}>"

    @property
    def department_name(self):
        return self.department.name if self.department else "General"
