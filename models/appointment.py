"""Appointments linking patients, doctors and departments."""
from datetime import datetime
from utils.time import utcnow

from database.db import db


class Appointment(db.Model):
    __tablename__ = "appointments"

    STATUS_PENDING = "pending"
    STATUS_ACCEPTED = "accepted"
    STATUS_REJECTED = "rejected"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False
    )
    department_id = db.Column(
        db.Integer, db.ForeignKey("departments.id", ondelete="SET NULL"), nullable=True
    )

    appointment_date = db.Column(db.Date, nullable=False, index=True)
    appointment_time = db.Column(db.String(10), nullable=False)
    status = db.Column(
        db.String(20), default=STATUS_PENDING, nullable=False, index=True
    )
    reason = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime, default=utcnow, onupdate=utcnow, nullable=False
    )

    prescription = db.relationship(
        "Prescription", backref="appointment", uselist=False
    )

    def __repr__(self):
        return f"<Appointment #{self.id} {self.status}>"

    @property
    def is_past(self):
        today = utcnow().date()
        return self.appointment_date < today

    @property
    def badge_class(self):
        return {
            self.STATUS_PENDING: "warning",
            self.STATUS_ACCEPTED: "success",
            self.STATUS_REJECTED: "danger",
            self.STATUS_COMPLETED: "info",
            self.STATUS_CANCELLED: "secondary",
        }.get(self.status, "secondary")
