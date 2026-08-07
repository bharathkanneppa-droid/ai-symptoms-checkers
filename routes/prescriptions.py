"""Prescription viewing and PDF download."""
from flask import (
    Blueprint, Response, flash, redirect, render_template, url_for,
)
from flask_login import current_user

from models import Prescription
from prescriptions.pdf import build_prescription_pdf
from utils.decorators import patient_required

prescriptions_bp = Blueprint("prescriptions", __name__, url_prefix="/prescriptions")


def _ensure_owner(prescription):
    """Patients may only access their own prescriptions."""
    if prescription.patient_id != current_user.patient.id:
        return None
    return prescription


@prescriptions_bp.route("/")
@patient_required
def index():
    prescriptions = (
        Prescription.query.filter_by(patient_id=current_user.patient.id)
        .order_by(Prescription.created_at.desc())
        .all()
    )
    return render_template("patient/prescriptions.html", prescriptions=prescriptions)


@prescriptions_bp.route("/<int:prescription_id>")
@patient_required
def detail(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    if not _ensure_owner(prescription):
        flash("You don't have access to that prescription.", "danger")
        return redirect(url_for("prescriptions.index"))
    return render_template(
        "patient/prescription_detail.html", prescription=prescription
    )


@prescriptions_bp.route("/<int:prescription_id>/download")
@patient_required
def download(prescription_id):
    prescription = Prescription.query.get_or_404(prescription_id)
    if not _ensure_owner(prescription):
        flash("You don't have access to that prescription.", "danger")
        return redirect(url_for("prescriptions.index"))

    pdf_bytes = build_prescription_pdf(prescription)
    filename = f"prescription_{prescription_id}.pdf"
    return Response(
        pdf_bytes,
        mimetype="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
