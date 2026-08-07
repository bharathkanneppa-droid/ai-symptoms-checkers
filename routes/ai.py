"""AI Doctor: conversational chat + direct symptom prediction endpoints."""
import json

from flask import (
    Blueprint, jsonify, render_template, request, session,
)
from flask_login import current_user, login_required

from ai.predictor import get_predictor
from chatbot.engine import get_bot
from chatbot.symptom_db import CONDITIONS
from database.db import db
from models import ChatHistory, PredictionHistory
from utils.decorators import patient_required

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

STATE_KEY = "ai_doctor_state"


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
@ai_bp.route("/chat")
@patient_required
def chat():
    history = (
        ChatHistory.query.filter_by(user_id=current_user.id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    return render_template("patient/ai_chat.html", history=history)


@ai_bp.route("/predict")
@patient_required
def predict_page():
    predictor = get_predictor()
    return render_template(
        "patient/predict.html",
        symptoms=predictor.supported_symptoms(),
    )


# --------------------------------------------------------------------------- #
# API
# --------------------------------------------------------------------------- #
@ai_bp.route("/api/chat", methods=["POST"])
@login_required
def api_chat():
    """Handle one turn of the conversational symptom checker."""
    data = request.get_json(silent=True) or {}
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "Empty message"}), 400

    state = dict(session.get(STATE_KEY, {}))
    result = get_bot().turn(message, state)

    # Persist the conversation transcript.
    db.session.add(ChatHistory(user_id=current_user.id, role="user", message=message))
    db.session.add(
        ChatHistory(
            user_id=current_user.id,
            role="assistant",
            message=result["reply"],
            symptoms_json=json.dumps(result["symptoms"]),
            prediction_json=json.dumps(result["prediction"])
            if result["prediction"] else None,
        )
    )

    # Save a prediction record for the patient's medical history.
    if result["prediction"] and current_user.patient:
        db.session.add(
            PredictionHistory(
                patient_id=current_user.patient.id,
                symptoms_json=json.dumps(result["symptoms"]),
                prediction_json=json.dumps(result["prediction"]),
                source="chat",
                is_emergency=result["emergency"],
            )
        )
    db.session.commit()

    # Persist next-turn state, or clear it if the user reset the chat.
    if result["reset"]:
        session.pop(STATE_KEY, None)
    else:
        session[STATE_KEY] = result["state"]

    return jsonify(result)


@ai_bp.route("/api/predict", methods=["POST"])
@login_required
def api_predict():
    """Direct prediction from a selected symptom list (checkbox form)."""
    data = request.get_json(silent=True) or {}
    symptom_keys = [s for s in data.get("symptoms", []) if s]

    predictor = get_predictor()
    supported = set(predictor.all_symptoms())
    symptom_keys = [s for s in symptom_keys if s in supported]
    if not symptom_keys:
        return jsonify({"error": "Select at least one valid symptom."}), 400

    result = predictor.predict(symptom_keys)
    top = result[0] if result else {}
    meta = CONDITIONS.get(top.get("disease"), {})
    emergency = bool(meta.get("emergency")) or any(
        s in {"shortness_of_breath", "chest_pain", "blood_in_urine"}
        for s in symptom_keys
    )

    if current_user.patient:
        db.session.add(
            PredictionHistory(
                patient_id=current_user.patient.id,
                symptoms_json=json.dumps(symptom_keys),
                prediction_json=json.dumps(result),
                source="form",
                is_emergency=emergency,
            )
        )
        db.session.commit()

    return jsonify({
        "symptoms": symptom_keys,
        "prediction": result,
        "specialist": meta.get("specialist"),
        "emergency": emergency,
        "disclaimer": "Educational result only - not medical advice.",
    })


@ai_bp.route("/api/reset", methods=["POST"])
@login_required
def api_reset():
    session.pop(STATE_KEY, None)
    return jsonify({"ok": True})
