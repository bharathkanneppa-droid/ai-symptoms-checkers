"""Prescriptions with a header and one-or-more medicine items."""
from datetime import datetime
from utils.time import utcnow

from database.db import db


class Prescription(db.Model):
    __tablename__ = "prescriptions"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True
    )
    appointment_id = db.Column(
        db.Integer, db.ForeignKey("appointments.id", ondelete="SET NULL"), nullable=True
    )

    diagnosis = db.Column(db.String(200), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    follow_up_in_days = db.Column(db.Integer, nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    items = db.relationship(
        "PrescriptionItem", backref="prescription", lazy="selectin",
        cascade="all, delete-orphan", order_by="PrescriptionItem.id",
    )

    def __repr__(self):
        return f"<Prescription #{self.id}>"

    @property
    def item_count(self):
        return len(self.items)


class PrescriptionItem(db.Model):
    __tablename__ = "prescription_items"

    id = db.Column(db.Integer, primary_key=True)
    prescription_id = db.Column(
        db.Integer, db.ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False
    )

    medicine_name = db.Column(db.String(120), nullable=False)
    dosage = db.Column(db.String(60), nullable=True)
    frequency = db.Column(db.String(60), nullable=True)
    duration = db.Column(db.String(60), nullable=True)
    instructions = db.Column(db.String(200), nullable=True)

    def __repr__(self):
        return f"<PrescriptionItem {self.medicine_name}>"
