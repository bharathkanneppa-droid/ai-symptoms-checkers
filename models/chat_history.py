"""Persistent transcript for the AI Doctor chat."""
import json
from datetime import datetime
from utils.time import utcnow

from database.db import db


class ChatHistory(db.Model):
    __tablename__ = "chat_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    role = db.Column(db.String(20), nullable=False)  # "user" | "assistant"
    message = db.Column(db.Text, nullable=False)
    # Structured symptom list that was active when the assistant replied.
    symptoms_json = db.Column(db.Text, nullable=True)
    prediction_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    def __repr__(self):
        return f"<ChatHistory #{self.id} {self.role}>"

    @property
    def symptoms(self):
        return json.loads(self.symptoms_json) if self.symptoms_json else []

    @property
    def prediction(self):
        return json.loads(self.prediction_json) if self.prediction_json else None
