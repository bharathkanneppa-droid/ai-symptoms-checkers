"""Google Gemini chat client for the AI Doctor conversation.

Uses Gemini's REST API directly (via ``requests``) so we avoid pulling in the
full ``google-generativeai`` SDK. When no API key is configured the app falls
back to the built-in rule-based symptom bot (see routes/ai.py).
"""
import json
import logging

import requests

from config import Config

logger = logging.getLogger(__name__)

API_ENDPOINT = (
    "https://generativelanguage.googleapis.com/v1beta/models/"
    "{model}:generateContent"
)

SYSTEM_PROMPT = (
    "You are MediAssist AI, a friendly, educational AI healthcare assistant. "
    "Talk with the user about their symptoms in a natural, caring, two-way "
    "conversation. Ask follow-up questions one at a time (onset, duration, "
    "severity, aggravating factors). Keep answers concise, warm and easy to "
    "understand.\n\n"
    "IMPORTANT RULES:\n"
    "- You are NOT a doctor and you do NOT diagnose. Always end with a clear "
    "disclaimer that your advice is educational and not medical advice.\n"
    "- If symptoms sound urgent or life-threatening (chest pain, severe "
    "difficulty breathing, heavy bleeding, loss of consciousness, severe "
    "abdominal pain), strongly urge the user to seek emergency care.\n"
    "- Recommend seeing a specialist when appropriate.\n"
    "- If the user asks to 'predict' or 'diagnose', give the most likely "
    "conditions with appropriate caveats, based only on what they described.\n"
    "- Respond in plain text with short paragraphs and occasional line breaks. "
    "No markdown headers or tables."
)


def is_enabled():
    """True when a Gemini API key is configured."""
    return bool(Config.GEMINI_API_KEY)


def chat(prompt, history=None, symptoms=None):
    """Send one turn to Gemini and return the assistant reply text.

    Args:
        prompt: the latest user message.
        history: optional list of {"role": "user"|"model", "text": ...} turns.
        symptoms: optional list of recognized symptom keys (informational).

    Returns:
        str reply, or raises GeminiError on failure.
    """
    contents = []
    if history:
        for turn in history[-12:]:
            role = "model" if turn["role"] == "assistant" else "user"
            contents.append({
                "role": role,
                "parts": [{"text": turn["text"]}],
            })
    contents.append({"role": "user", "parts": [{"text": prompt}]})

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_PROMPT}],
        },
        "contents": contents,
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": 800,
            "topP": 0.9,
        },
    }
    if symptoms:
        payload["system_instruction"]["parts"][0]["text"] += (
            "\n\nRecognized symptom keywords so far: " + ", ".join(symptoms)
        )

    url = API_ENDPOINT.format(model=Config.GEMINI_MODEL)
    resp = requests.post(
        url,
        params={"key": Config.GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=60,
    )
    if resp.status_code != 200:
        logger.error("Gemini API error %s: %s", resp.status_code, resp.text[:500])
        raise GeminiError(f"Gemini API returned {resp.status_code}")

    data = resp.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"].strip()
    except (KeyError, IndexError, TypeError):
        logger.error("Unexpected Gemini response: %s", json.dumps(data)[:500])
        raise GeminiError("Could not parse Gemini response")


class GeminiError(Exception):
    """Raised when the Gemini API call fails."""
