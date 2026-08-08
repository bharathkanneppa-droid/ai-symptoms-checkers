"""Conversation sessions for the AI Doctor chat.

Each chat session groups ChatHistory rows so a patient can pause a
consultation and resume it later (the session picker in the chat UI).
"""
from utils.time import utcnow

from database.db import db


class ChatSession(db.Model):
    __tablename__ = "chat_sessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )

    title = db.Column(db.String(120), nullable=True)  # first user message
    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=utcnow, onupdate=utcnow, nullable=False)

    messages = db.relationship(
        "ChatHistory",
        backref="chat_session",
        cascade="all, delete-orphan",
        order_by="ChatHistory.id",
    )

    def __repr__(self):
        return f"<ChatSession #{self.id}>"
