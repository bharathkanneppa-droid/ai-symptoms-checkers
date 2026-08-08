"""AI Doctor: conversational chat + direct symptom prediction endpoints."""
import json
import logging

from flask import (
    Blueprint, jsonify, render_template, request, session,
)
from flask_login import current_user, login_required

from ai import gemini
from ai.predictor import get_predictor
from chatbot.engine import get_bot
from chatbot.symptom_db import CONDITIONS
from database.db import db
from models import ChatHistory, PredictionHistory
from utils.decorators import patient_required

logger = logging.getLogger(__name__)

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

    # Live Gemini conversations keep a rolling transcript in the session.
    transcript = list(session.get("ai_transcript", []))[-12:]
    result = _run_engine(message, transcript)

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

    # Keep the transcript up to date for the next Gemini turn.
    transcript.append({"role": "user", "text": message})
    transcript.append({"role": "assistant", "text": result["reply"]})
    session["ai_transcript"] = transcript[-20:]
    session.modified = True

    # Persist next-turn state for the rule-based bot, or clear it on reset.
    if result["reset"]:
        session.pop("ai_doctor_state", None)
    else:
        session["ai_doctor_state"] = result["state"]

    return jsonify(result)


def _run_engine(message, transcript):
    """Drive the conversation with Gemini when configured; else the rule bot."""
    state = dict(session.get("ai_doctor_state", {}))

    if gemini.is_enabled():
        try:
            symptoms = state.get("symptoms", [])
            reply = gemini.chat(message, history=transcript, symptoms=symptoms)
            return {
                "reply": reply,
                "symptoms": symptoms,
                "negatives": state.get("negatives", []),
                "prediction": None,
                "specialist": None,
                "emergency": False,
                "finished": False,
                "reset": False,
                "turns": state.get("turns", 0) + 1,
                "state": state,
            }
        except gemini.GeminiError:
            logger.warning("Gemini unavailable, falling back to rule-based bot")

    return get_bot().turn(message, state)


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
    session.pop("ai_transcript", None)
    return jsonify({"ok": True})
