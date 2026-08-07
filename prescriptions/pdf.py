"""PDF generation for prescriptions using ReportLab."""
import io
from datetime import datetime
from utils.time import utcnow

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

from config import Config


def _style_rows(rows):
    styles = getSampleStyleSheet()
    rows[0].insert(0, Paragraph("<b>#</b>", styles["BodyText"]))
    styled = [rows[0]]
    for i, row in enumerate(rows[1:], start=1):
        styled.append(
            [Paragraph(f"<b>{i}</b>", styles["BodyText"])]
            + [Paragraph(str(cell), styles["BodyText"]) for cell in row]
        )
    return styled


def build_prescription_pdf(prescription):
    """Return bytes for a professional-looking prescription PDF."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        topMargin=18 * mm, bottomMargin=18 * mm,
        leftMargin=16 * mm, rightMargin=16 * mm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle("TitleX", parent=styles["Title"], textColor=colors.HexColor("#0d6efd"))
    small = ParagraphStyle("Small", parent=styles["BodyText"], fontSize=9, textColor=colors.HexColor("#6c757d"))

    story = []

    # Header
    story.append(Paragraph(Config.APP_NAME, title))
    story.append(Paragraph("AI Healthcare Management System &nbsp;|&nbsp; 100 Health Street, Your City", small))
    story.append(Spacer(1, 2 * mm))

    # Meta info
    now = utcnow()
    doc_id = f"RX-{prescription.id:05d}-{now.year}"
    meta = Table(
        [
            [Paragraph("<b>Patient:</b>", styles["BodyText"]), Paragraph(prescription.patient.full_name, styles["BodyText"]),
             Paragraph("<b>Date:</b>", styles["BodyText"]), Paragraph(prescription.created_at.strftime("%d %b %Y"), styles["BodyText"])],
            [Paragraph("<b>Doctor:</b>", styles["BodyText"]), Paragraph(prescription.doctor.full_name if prescription.doctor else "Hospital Doctor", styles["BodyText"]),
             Paragraph("<b>Rx No:</b>", styles["BodyText"]), Paragraph(doc_id, styles["BodyText"])],
            [Paragraph("<b>Specialization:</b>", styles["BodyText"]), Paragraph(prescription.doctor.specialization or "General", styles["BodyText"]),
             Paragraph("", styles["BodyText"]), Paragraph("", styles["BodyText"])],
        ],
        colWidths=[30 * mm, 85 * mm, 25 * mm, 50 * mm],
    )
    meta.setStyle(TableStyle([
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8f9fa")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(meta)
    story.append(Spacer(1, 6 * mm))

    # Diagnosis
    story.append(Paragraph("Diagnosis", ParagraphStyle("H", parent=styles["Heading4"], textColor=colors.HexColor("#0d6efd"))))
    story.append(Paragraph(prescription.diagnosis, styles["BodyText"]))
    story.append(Spacer(1, 5 * mm))

    # Medicine table
    story.append(Paragraph("Medicines", ParagraphStyle("H2", parent=styles["Heading4"], textColor=colors.HexColor("#0d6efd"))))
    header = ["Medicine", "Dosage", "Frequency", "Duration", "Instructions"]
    rows = [header]
    for item in prescription.items:
        rows.append([item.medicine_name, item.dosage or "-", item.frequency or "-",
                     item.duration or "-", item.instructions or "-"])
    items_table = Table(_style_rows(rows), repeatRows=1)
    items_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#dee2e6")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8f9fa")]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(items_table)
    story.append(Spacer(1, 6 * mm))

    if prescription.notes:
        story.append(Paragraph("Notes", ParagraphStyle("H3", parent=styles["Heading4"], textColor=colors.HexColor("#0d6efd"))))
        story.append(Paragraph(prescription.notes, styles["BodyText"]))
        story.append(Spacer(1, 6 * mm))

    if prescription.follow_up_in_days:
        story.append(Paragraph(
            f"<b>Follow up:</b> please return in {prescription.follow_up_in_days} day(s).",
            styles["BodyText"],
        ))
        story.append(Spacer(1, 8 * mm))

    # Signature
    sig = Table(
        [[Paragraph("Doctor's Signature", styles["BodyText"]), Paragraph("", styles["BodyText"])]],
        colWidths=[90 * mm, 100 * mm],
    )
    story.append(sig)
    story.append(Spacer(1, 10 * mm))
    story.append(Paragraph(
        "This prescription is issued based on an in-person/virtual consultation and is for the "
        "named patient only. Not for resale.",
        ParagraphStyle("Fine", parent=small, fontSize=8, textColor=colors.HexColor("#adb5bd")),
    ))

    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
