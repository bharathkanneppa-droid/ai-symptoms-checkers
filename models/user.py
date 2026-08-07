"""Flask-Login compatible User model (one account, three roles)."""
from datetime import datetime
from utils.time import utcnow

from flask_login import UserMixin
from database.db import db


class User(UserMixin, db.Model):
    __tablename__ = "users"

    ROLE_PATIENT = "patient"
    ROLE_DOCTOR = "doctor"
    ROLE_ADMIN = "admin"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default=ROLE_PATIENT, index=True)
    is_active_flag = db.Column("is_active", db.Boolean, default=True, nullable=False)

    is_email_verified = db.Column(db.Boolean, default=False, nullable=False)
    verification_token = db.Column(db.String(128), nullable=True)
    reset_token = db.Column(db.String(128), nullable=True)
    reset_token_expires = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)
    last_login_at = db.Column(db.DateTime, nullable=True)

    # Relationships (lazy loaded; foreign keys defined on the child models).
    patient = db.relationship("Patient", backref="user", uselist=False)
    doctor = db.relationship("Doctor", backref="user", uselist=False)
    notifications = db.relationship(
        "Notification", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )
    chat_messages = db.relationship(
        "ChatHistory", backref="user", lazy="dynamic", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username} ({self.role})>"

    @property
    def is_active(self):
        """Flask-Login hook: an admin can disable an account."""
        return self.is_active_flag

    @property
    def is_patient(self):
        return self.role == self.ROLE_PATIENT

    @property
    def is_doctor(self):
        return self.role == self.ROLE_DOCTOR

    @property
    def is_admin(self):
        return self.role == self.ROLE_ADMIN

    @property
    def display_name(self):
        """Human friendly name depending on the role."""
        if self.is_patient and self.patient:
            return self.patient.full_name or self.username
        if self.is_doctor and self.doctor:
            return self.doctor.full_name or self.username
        return self.username
