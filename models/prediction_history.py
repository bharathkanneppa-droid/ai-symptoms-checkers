"""Log of AI symptom-checker predictions per patient (audit trail + history)."""
import json
from datetime import datetime
from utils.time import utcnow

from database.db import db


class PredictionHistory(db.Model):
    __tablename__ = "prediction_history"

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(
        db.Integer, db.ForeignKey("patients.id", ondelete="CASCADE"), nullable=False
    )

    symptoms_json = db.Column(db.Text, nullable=False)
    prediction_json = db.Column(db.Text, nullable=False)  # top-5 list
    source = db.Column(db.String(20), default="chat", nullable=False)  # chat | form
    is_emergency = db.Column(db.Boolean, default=False, nullable=False)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def __repr__(self):
        return f"<PredictionHistory #{self.id}>"

    @property
    def symptoms(self):
        return json.loads(self.symptoms_json)

    @property
    def prediction(self):
        return json.loads(self.prediction_json)
