"""Blueprints package. Register every blueprint on the app here."""
from routes.admin import admin_bp
from routes.ai import ai_bp
from routes.appointments import appointments_bp
from routes.auth import auth_bp
from routes.doctor import doctor_bp
from routes.main import main_bp
from routes.notifications import notifications_bp
from routes.patient import patient_bp
from routes.prescriptions import prescriptions_bp


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(patient_bp)
    app.register_blueprint(doctor_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(prescriptions_bp)
    app.register_blueprint(notifications_bp)


__all__ = ["register_blueprints"]
