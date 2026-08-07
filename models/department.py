"""Departments a doctor can belong to."""
from datetime import datetime
from utils.time import utcnow

from database.db import db


class Department(db.Model):
    __tablename__ = "departments"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(60), nullable=True, default="bi-activity")

    created_at = db.Column(db.DateTime, default=utcnow, nullable=False)

    doctors = db.relationship("Doctor", backref="department", lazy="dynamic")

    def __repr__(self):
        return f"<Department {self.name}>"
