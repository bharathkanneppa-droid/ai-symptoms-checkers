"""AI Doctor: conversational chat + direct symptom prediction endpoints.

Conversations are grouped into chat sessions (see models.ChatSession) so a
patient can pause a consultation and resume it from the session picker in the
chat UI. Per-session bot state and Gemini transcripts are scoped by session.
"""
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
from models import ChatHistory, ChatSession, PredictionHistory
from utils.decorators import patient_required
from utils.time import utcnow

logger = logging.getLogger(__name__)

ai_bp = Blueprint("ai", __name__, url_prefix="/ai")

STATES_KEY = "ai_states"  # per-session bot state, keyed by session id
SESSION_KEY = "ai_session_id"  # active chat session in the Flask session


# --------------------------------------------------------------------------- #
# Pages
# --------------------------------------------------------------------------- #
@ai_bp.route("/chat")
@patient_required
def chat():
    sessions = (
        ChatSession.query.filter_by(user_id=current_user.id)
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        .all()
    )
    active_id = request.args.get("session", type=int) or session.get(SESSION_KEY)
    active = None
    if active_id:
        active = ChatSession.query.filter_by(
            id=active_id, user_id=current_user.id
        ).first()
    if active is None and sessions:
        active = sessions[0]
    if active:
        session[SESSION_KEY] = active.id

    history = []
    if active:
        history = (
            ChatHistory.query.filter_by(user_id=current_user.id, session_id=active.id)
            .order_by(ChatHistory.id)
            .all()
        )
    return render_template(
        "patient/ai_chat.html",
        history=history,
        sessions=sessions,
        active=active,
    )


@ai_bp.route("/predict")
@patient_required
def predict_page():
    predictor = get_predictor()
    return render_template(
        "patient/predict.html",
        symptoms=predictor.supported_symptoms(),
    )


# --------------------------------------------------------------------------- #
# Session management
# --------------------------------------------------------------------------- #
@ai_bp.route("/api/sessions", methods=["GET"])
@login_required
def api_sessions():
    """List the current user's conversations, most recent first."""
    sessions = (
        ChatSession.query.filter_by(user_id=current_user.id)
        .order_by(ChatSession.updated_at.desc(), ChatSession.id.desc())
        .all()
    )
    active_id = session.get(SESSION_KEY)
    return jsonify([
        {
            "id": s.id,
            "title": s.title or "New chat",
            "updated_at": s.updated_at.strftime("%Y-%m-%d %H:%M"),
            "active": s.id == active_id,
        }
        for s in sessions
    ])


@ai_bp.route("/api/sessions", methods=["POST"])
@login_required
def api_new_session():
    """Start a fresh chat session and make it the active one."""
    chat_session = ChatSession(user_id=current_user.id)
    db.session.add(chat_session)
    db.session.commit()
    session[SESSION_KEY] = chat_session.id
    _clear_session_state(chat_session.id)
    return jsonify({"id": chat_session.id, "title": "New chat"})


@ai_bp.route("/api/sessions/<int:chat_session_id>/messages", methods=["GET"])
@login_required
def api_session_messages(chat_session_id):
    """Load a conversation's messages and resume it as the active session."""
    chat_session = ChatSession.query.filter_by(
        id=chat_session_id, user_id=current_user.id
    ).first_or_404()
    session[SESSION_KEY] = chat_session.id
    messages = (
        ChatHistory.query.filter_by(
            user_id=current_user.id, session_id=chat_session.id
        )
        .order_by(ChatHistory.id)
        .all()
    )
    return jsonify([{"role": m.role, "message": m.message} for m in messages])


@ai_bp.route("/api/sessions/<int:chat_session_id>", methods=["DELETE"])
@login_required
def api_delete_session(chat_session_id):
    """Delete a conversation and its messages."""
    chat_session = ChatSession.query.filter_by(
        id=chat_session_id, user_id=current_user.id
    ).first_or_404()
    db.session.delete(chat_session)
    db.session.commit()
    if session.get(SESSION_KEY) == chat_session.id:
        session.pop(SESSION_KEY, None)
    return jsonify({"ok": True})


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

    chat_session = _resolve_session(data.get("session_id"))
    session[SESSION_KEY] = chat_session.id

    # Rebuild Gemini context from persisted history so resumes work seamlessly.
    prior = (
        ChatHistory.query.filter_by(
            user_id=current_user.id, session_id=chat_session.id
        )
        .order_by(ChatHistory.id.desc())
        .limit(12)
        .all()
    )
    transcript = [{"role": m.role, "text": m.message} for m in reversed(prior)]

    states = session.get(STATES_KEY, {})
    state = dict(states.get(str(chat_session.id), {}))
    result = _run_engine(message, transcript, state)

    # Persist the conversation transcript.
    db.session.add(
        ChatHistory(
            user_id=current_user.id,
            session_id=chat_session.id,
            role="user",
            message=message,
        )
    )
    db.session.add(
        ChatHistory(
            user_id=current_user.id,
            session_id=chat_session.id,
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

    # Name the session after the patient's first message.
    if not chat_session.title:
        chat_session.title = message[:80]
    chat_session.updated_at = utcnow()
    db.session.commit()

    # Keep per-session next-turn state for the rule-based bot.
    if result["reset"]:
        states.pop(str(chat_session.id), None)
    else:
        states[str(chat_session.id)] = result["state"]
    session[STATES_KEY] = states
    session.modified = True

    result["session_id"] = chat_session.id
    return jsonify(result)


def _resolve_session(session_id):
    """Return the active session for the current user, creating one if needed."""
    if session_id:
        chat_session = ChatSession.query.filter_by(
            id=int(session_id), user_id=current_user.id
        ).first()
        if chat_session:
            return chat_session
    active_id = session.get(SESSION_KEY)
    if active_id:
        chat_session = ChatSession.query.filter_by(
            id=int(active_id), user_id=current_user.id
        ).first()
        if chat_session:
            return chat_session
    chat_session = ChatSession(user_id=current_user.id)
    db.session.add(chat_session)
    db.session.flush()
    return chat_session


def _clear_session_state(chat_session_id):
    states = session.get(STATES_KEY, {})
    states.pop(str(chat_session_id), None)
    session[STATES_KEY] = states
    session.modified = True


def _run_engine(message, transcript, state):
    """Drive the conversation with Gemini when configured; else the rule bot."""
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
    active_id = session.get(SESSION_KEY)
    if active_id:
        _clear_session_state(active_id)
    return jsonify({"ok": True})
