"""Doctor-entered clinical history records for a patient."""
from datetime import datetime
from utils.time import utcnow

from database.db import db


class MedicalHistory(db.Model):
    __tablename__ = "medical_history"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("doctors.id", ondelete="SET NULL"), nullable=True
    )

    diagnosis = db.Column(db.String(200), nullable=False)
    symptoms = db.Column(db.Text, nullable=True)
    treatment = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def __repr__(self):
        return f"<MedicalHistory #{self.id} {self.diagnosis}>"
