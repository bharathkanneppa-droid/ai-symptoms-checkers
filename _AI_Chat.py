"""Symptom Chat Assistant - LLM-powered version.

Uses the Anthropic API (Claude) to hold an open-ended conversation about
symptoms, while a fixed system prompt keeps it in a safe, non-diagnostic,
triage-and-education role.

EDUCATIONAL DEMO ONLY. Not a diagnosis and not medical advice.
Requires an Anthropic API key (https://console.anthropic.com).
"""

import streamlit as st
from anthropic import Anthropic

MODEL_NAME = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are a health-education chat assistant for a student capstone \
project. Your role is strictly limited:

1. You are NOT a doctor and must never diagnose, prescribe medication, or tell \
someone what condition they "have." You can discuss possible/common explanations \
in general educational terms only ("symptoms like X are commonly associated with \
things like Y, but only a doctor can tell you what's actually going on").

2. Red-flag symptoms (chest pain, difficulty breathing, severe bleeding, stroke \
signs, suicidal thoughts, loss of consciousness, severe allergic reaction, etc.) \
must ALWAYS get an immediate, clear instruction to seek emergency care now — \
before anything else in your reply.

3. For non-emergency symptoms, you can offer general self-care information \
(rest, hydration, OTC options people commonly use) and explain when it's \
worth seeing a doctor (e.g. symptom duration, severity, red flags to watch for).

4. Always keep a warm, clear, conversational tone — you're allowed to ask \
clarifying questions like a knowledgeable friend would (how long, how severe, \
any other symptoms).

5. Every response should make clear, without being repetitive or robotic, that \
this is general information and not a substitute for seeing a real doctor.

6. Never claim certainty about what's wrong with someone. Use hedged, \
educational language throughout.
"""


def get_client():
    api_key = st.session_state.get("api_key", "")
    if not api_key:
        return None
    return Anthropic(api_key=api_key)


def main():
    st.set_page_config(page_title="Symptom Chat Assistant (AI)", page_icon="🩺")
    st.title("🩺 Symptom Chat Assistant")
    st.caption("LLM-powered capstone demo — talk about how you're feeling")

    st.warning(
        "⚠️ **Educational demo only - not medical advice.** This assistant "
        "cannot diagnose you. For real concerns, consult a qualified doctor; "
        "for anything urgent, call your local emergency services."
    )

    with st.sidebar:
        st.subheader("Setup")
        api_key = st.text_input(
            "Anthropic API key",
            type="password",
            help="Get one at console.anthropic.com. Not stored anywhere except this session.",
        )
        st.session_state.api_key = api_key
        if st.button("🔄 Start over"):
            st.session_state.messages = []
            st.rerun()

    if not api_key:
        st.info("Enter your Anthropic API key in the sidebar to start chatting.")
        st.stop()

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    user_input = st.chat_input("Describe how you're feeling...")
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.markdown(user_input)

        client = get_client()
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_reply = ""
            try:
                with client.messages.stream(
                    model=MODEL_NAME,
                    max_tokens=800,
                    system=SYSTEM_PROMPT,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in st.session_state.messages
                    ],
                ) as stream:
                    for text in stream.text_stream:
                        full_reply += text
                        placeholder.markdown(full_reply + "▌")
                placeholder.markdown(full_reply)
            except Exception as e:
                full_reply = f"Something went wrong calling the API: {e}"
                placeholder.markdown(full_reply)

        st.session_state.messages.append({"role": "assistant", "content": full_reply})


if __name__ == "__main__":
    main()
