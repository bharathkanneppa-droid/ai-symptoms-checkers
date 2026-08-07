"""Rule-based conversational engine behind the AI Doctor chat.

The engine is intentionally simple and transparent:

* It recognises symptoms from free text (fuzzy alias matching over the 53
  model features).
* It asks a *duration* question for the first reported symptom, then probes
  related symptoms (drawn from the conditions that share the reported
  symptoms), one at a time.
* When it has enough context (or the user asks), it hands the collected
  symptom list to the RandomForest model and returns the top-5 predictions.

The engine itself is stateless: every turn it receives the conversation state
and returns the updated state alongside the reply, so the caller can persist it
(Flask session / ChatHistory rows).
"""
import re

from ai.predictor import get_predictor
from chatbot.symptom_db import (
    SYMPTOMS,
    CONDITIONS,
    symptom_aliases,
    related_symptoms,
)

DISCLAIMER = (
    "I'm an educational AI assistant, not a doctor. My suggestions are based on "
    "statistical patterns and are not medical advice. For anything urgent, call "
    "emergency services."
)

CRITICAL_SYMPTOMS = {"shortness_of_breath", "chest_pain", "blood_in_urine"}

MAX_PROBES = 8  # cap on yes/no follow-up questions per conversation

NEGATION_RE = re.compile(r"\b(no|not|never|don'?t|do not|without|cannot|can'?t)\b")


def _normalize(text):
    return re.sub(r"[^a-z0-9\s]", " ", text.lower())


def _extract_symptoms(text, aliases):
    """Return (present, absent) symptom keys mentioned in free text."""
    present, absent = set(), set()
    for alias, key in aliases.items():
        if alias not in text:
            continue
        # Look slightly around the alias for a negation word.
        idx = text.find(alias)
        window = text[max(0, idx - 30): idx + len(alias) + 5]
        if NEGATION_RE.search(window) or " not " in (" " + window + " "):
            absent.add(key)
        else:
            present.add(key)
    return present, absent


def _empty_state(turns=0):
    return {
        "symptoms": [],
        "negatives": [],
        "duration": {},
        "asked": [],
        "pending": None,
        "turns": turns,
    }


class SymptomBot:
    """Holds no server-side state; state lives in the Flask session."""

    GREETING = (
        "Hello.\n\nI'm your AI Healthcare Assistant. " + DISCLAIMER + "\n\n"
        "What symptoms are you experiencing?"
    )

    def __init__(self, aliases=None):
        self.aliases = aliases or symptom_aliases()
        self.predictor = get_predictor()

    # ------------------------------------------------------------------ #
    # Main entry point
    # ------------------------------------------------------------------ #
    def turn(self, message, state):
        """Process one user message given the persisted conversation state.

        Args:
            message: raw user text.
            state: dict with keys symptoms, negatives, duration, asked,
                   pending, turns.

        Returns:
            dict with reply, symptoms, negatives, prediction (or None),
            specialist (or None), finished, reset, emergency, state.
        """
        text = _normalize(message)
        st = dict(state or {})
        symptoms = list(st.get("symptoms", []))
        negatives = list(st.get("negatives", []))
        duration = dict(st.get("duration", {}))
        asked = list(st.get("asked", []))
        pending = st.get("pending")
        turns = st.get("turns", 0) + 1

        # --- Commands ---------------------------------------------------
        if re.search(r"\b(reset|start over|new chat|restart)\b", text):
            fresh = _empty_state()
            return self._reply("Starting a fresh consultation.\n\n" + self.GREETING,
                               state=fresh, reset=True)

        if re.search(r"\b(diagnose|predict|analyze|result|done|finish|get result)\b", text):
            return self._predict(symptoms, negatives, duration, asked, turns, forced=True)

        if re.search(r"\b(hi|hello|hey|namaste)\b", text) and not symptoms:
            return self._reply(self.GREETING, state=st, turns=turns)

        if re.search(r"\b(thanks|thank you|thnx)\b", text):
            return self._reply(
                "You're welcome! Stay well. Type 'reset' to start a new consultation.",
                state=st, turns=turns)

        if re.search(r"\b(bye|goodbye|see you)\b", text):
            return self._reply("Take care! Type 'reset' anytime to start over.",
                               state=st, turns=turns)

        if re.search(r"\b(help|what can you do|how does this work)\b", text):
            return self._reply(
                "Describe your symptoms in plain words, e.g. \"I have fever and a cough\". "
                "I'll ask a few follow-up questions, then show the most likely conditions "
                "and recommend a specialist. " + DISCLAIMER,
                state=st, turns=turns)

        # --- Answer a pending question first -----------------------------
        if pending:
            target = pending.get("symptom")
            if pending.get("type") == "probe" and self._is_yes_no(text):
                if self._is_yes(text):
                    if target not in symptoms:
                        symptoms.append(target)
                else:
                    if target not in negatives:
                        negatives.append(target)
                if target not in asked:
                    asked.append(target)
                pending = None
            elif pending.get("type") == "duration":
                duration[target] = text.strip()
                pending = None

        # --- Extract symptoms from free text -----------------------------
        present, absent = _extract_symptoms(text, self.aliases)
        for key in present:
            if key not in symptoms:
                symptoms.append(key)
        for key in absent:
            if key not in negatives and key not in symptoms:
                negatives.append(key)

        # --- Decide the next question -------------------------------------
        if not symptoms:
            return self._reply(
                "I didn't catch any symptoms there. Could you describe how you're feeling? "
                "For example: \"I have fever and a headache\".",
                state=_snapshot(symptoms, negatives, duration, asked, pending, turns),
                turns=turns)

        if pending is None:
            if duration.get(symptoms[0]) is None:
                # First reported symptom: ask duration, like a real triage.
                pending = {"type": "duration", "symptom": symptoms[0]}
                return self._reply(
                    f"Since when have you had {self._label(symptoms[0])}?",
                    state=_snapshot(symptoms, negatives, duration, asked, pending, turns),
                    turns=turns)

            next_probe = self._next_probe(symptoms, negatives, asked)
            if next_probe is not None and turns < MAX_PROBES:
                pending = {"type": "probe", "symptom": next_probe}
                return self._reply(
                    SYMPTOMS[next_probe]["question"],
                    state=_snapshot(symptoms, negatives, duration, asked, pending, turns),
                    turns=turns)

        # --- Ran out of questions -> predict ------------------------------
        return self._predict(symptoms, negatives, duration, asked, turns)

    # ------------------------------------------------------------------ #
    # Prediction
    # ------------------------------------------------------------------ #
    def _predict(self, symptoms, negatives, duration, asked, turns, forced=False):
        if not symptoms:
            return self._reply(
                "I need at least one symptom to run an analysis. Please describe how you feel.",
                state=_snapshot(symptoms, negatives, duration, asked, None, turns),
                turns=turns)

        result = self.predictor.predict(symptoms)
        top = result[0] if result else {}
        condition = top.get("disease")
        meta = CONDITIONS.get(condition, {})
        emergency = (
            meta.get("emergency", False)
            or any(s in CRITICAL_SYMPTOMS for s in symptoms)
        )

        lines = ["I've analyzed your symptoms. Here are the top likely conditions:", ""]
        for i, item in enumerate(result, 1):
            bar = "=" * max(1, int(item["confidence"] / 10))
            lines.append(f"{i}. {item['disease']}  -  {item['confidence']}% confidence")
            lines.append(f"   {bar}")

        if meta:
            lines += [
                "",
                f"Recommended specialist: {meta['specialist']}",
                f"Suggestion: {meta['advice']}",
            ]

        if emergency:
            lines.append(
                "\nIMPORTANT: Some of your symptoms can be serious. Please seek medical "
                "attention promptly."
            )
        lines.append(
            "\n" + DISCLAIMER + "\nYou can book an appointment with a doctor from the "
            "appointments menu."
        )
        return {
            "reply": "\n".join(lines),
            "symptoms": list(symptoms),
            "negatives": list(negatives),
            "prediction": result,
            "specialist": meta.get("specialist"),
            "emergency": emergency,
            "finished": True,
            "reset": False,
            "turns": turns,
            "state": _snapshot(symptoms, negatives, duration, asked, None, turns),
        }

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _label(self, key):
        return SYMPTOMS.get(key, {}).get("label", key.replace("_", " ").title())

    def _next_probe(self, symptoms, negatives, asked):
        """Pick the most relevant symptom to ask about that wasn't asked yet."""
        for candidate in related_symptoms(symptoms):
            if candidate in symptoms or candidate in negatives or candidate in asked:
                continue
            return candidate
        return None

    @staticmethod
    def _is_yes_no(text):
        return bool(re.search(r"\b(yes|yeah|yep|no|nope|not really|nah)\b", text))

    @staticmethod
    def _is_yes(text):
        return bool(re.search(r"\b(yes|yeah|yep)\b", text))

    @staticmethod
    def _reply(reply, state=None, prediction=None, specialist=None, emergency=False,
               finished=False, reset=False, turns=None):
        state = state or _empty_state(turns or 0)
        return {
            "reply": reply,
            "symptoms": list(state.get("symptoms", [])),
            "negatives": list(state.get("negatives", [])),
            "prediction": prediction,
            "specialist": specialist,
            "emergency": emergency,
            "finished": finished,
            "reset": reset,
            "turns": state.get("turns", turns or 0),
            "state": state,
        }


def _snapshot(symptoms, negatives, duration, asked, pending, turns):
    return {
        "symptoms": list(symptoms),
        "negatives": list(negatives),
        "duration": dict(duration),
        "asked": list(asked),
        "pending": pending,
        "turns": turns,
    }


_bot = None


def get_bot():
    global _bot
    if _bot is None:
        _bot = SymptomBot()
    return _bot
