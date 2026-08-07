"""Weekly availability windows for each doctor.

day_of_week uses Python's convention: 0 = Monday ... 6 = Sunday.
If a doctor has no row for a given weekday, the default 09:00-17:00 window
applies. is_available=False means the doctor is off that day.
"""
from database.db import db


class DoctorAvailability(db.Model):
    __tablename__ = "doctor_availability"

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(
        db.Integer, db.ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False
    )

    day_of_week = db.Column(db.Integer, nullable=False)  # 0 (Mon) - 6 (Sun)
    is_available = db.Column(db.Boolean, default=True, nullable=False)
    start_time = db.Column(db.String(5), default="09:00", nullable=False)
    end_time = db.Column(db.String(5), default="17:00", nullable=False)

    __table_args__ = (db.UniqueConstraint("doctor_id", "day_of_week", name="uq_doctor_day"),)

    def __repr__(self):
        return f"<Availability D{self.doctor_id} day={self.day_of_week} {self.start_time}-{self.end_time}>"
