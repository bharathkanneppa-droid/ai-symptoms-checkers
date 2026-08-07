"""ORM models package.

The trained ML artifacts (classifier.joblib, symptom_list.joblib) shipped with
the original symptom-checker project also live in this folder and are loaded by
ai/predictor.py.
"""
from models.user import User
from models.patient import Patient
from models.doctor import Doctor
from models.department import Department
from models.appointment import Appointment
from models.medical_history import MedicalHistory
from models.prescription import Prescription, PrescriptionItem
from models.chat_history import ChatHistory
from models.notification import Notification
from models.doctor_availability import DoctorAvailability
from models.prediction_history import PredictionHistory

__all__ = [
    "User",
    "Patient",
    "Doctor",
    "Department",
    "Appointment",
    "MedicalHistory",
    "Prescription",
    "PrescriptionItem",
    "ChatHistory",
    "Notification",
    "DoctorAvailability",
    "PredictionHistory",
]
