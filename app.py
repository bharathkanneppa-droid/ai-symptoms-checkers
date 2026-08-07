"""Symptom Checker Assistant - a Streamlit demo app.

EDUCATIONAL DEMO ONLY. The predictions are statistical matches from a model
trained on synthetic data; this is not a diagnosis and not medical advice.
"""

from datetime import datetime
from pathlib import Path

import joblib
import pandas as pd
import streamlit as st

BASE_DIR = Path(__file__).resolve().parent
MODEL_PATH = BASE_DIR / "models" / "classifier.joblib"
SYMPTOM_LIST_PATH = BASE_DIR / "models" / "symptom_list.joblib"
TOP_N = 5
LOW_CONFIDENCE_THRESHOLD = 0.30  # below this, nudge the user to add more detail


@st.cache_resource
def load_model():
    model = joblib.load(MODEL_PATH)
    symptom_list = joblib.load(SYMPTOM_LIST_PATH)
    return model, symptom_list


SYMPTOM_LABELS = {
    "runny_nose": "Runny nose",
    "sneezing": "Sneezing",
    "sore_throat": "Sore throat",
    "cough": "Cough",
    "headache": "Headache",
    "fever": "Fever",
    "fatigue": "Fatigue",
    "nasal_congestion": "Nasal congestion",
    "body_aches": "Body aches",
    "chills": "Chills",
    "nausea": "Nausea",
    "vomiting": "Vomiting",
    "diarrhea": "Diarrhea",
    "abdominal_pain": "Abdominal pain",
    "watery_eyes": "Watery eyes",
    "itchy_eyes": "Itchy eyes",
    "skin_rash": "Skin rash",
    "frequent_urination": "Frequent urination",
    "burning_on_urination": "Burning on urination",
    "lower_back_pain": "Lower back pain",
    "dizziness": "Dizziness",
    "shortness_of_breath": "Shortness of breath",
    "chest_tightness": "Chest tightness",
    "loss_of_appetite": "Loss of appetite",
    "light_sensitivity": "Light sensitivity",
    "sound_sensitivity": "Sound sensitivity",
    "vision_disturbance": "Vision disturbance",
    "itchy_throat": "Itchy throat",
    "facial_pain": "Facial pain",
    "blood_in_urine": "Blood in urine",
    "difficulty_swallowing": "Difficulty swallowing",
    "wheezing": "Wheezing",
    "neck_stiffness": "Neck stiffness",
    "red_eyes": "Red eyes",
    "eye_discharge": "Eye discharge",
    "swelling_of_eyelids": "Swollen eyelids",
    "heartburn": "Heartburn",
    "regurgitation": "Regurgitation",
    "chest_pain": "Chest pain",
    "sour_taste_in_mouth": "Sour taste in mouth",
    "difficulty_sleeping": "Difficulty sleeping",
    "hard_stools": "Hard stools",
    "difficulty_passing_stool": "Difficulty passing stool",
    "bloating": "Bloating",
    "irritability": "Irritability",
    "difficulty_concentrating": "Difficulty concentrating",
    "dry_mouth": "Dry mouth",
    "dark_urine": "Dark urine",
    "muscle_cramps": "Muscle cramps",
    "ear_pain": "Ear pain",
    "ear_pressure": "Ear pressure",
    "difficulty_hearing": "Difficulty hearing",
    "itching": "Itching",
}


def human_label(symptom):
    """Map an internal symptom id to a human-readable label."""
    return SYMPTOM_LABELS.get(symptom, symptom.replace("_", " ").title())


def build_report_text(selected, ranking):
    """Plain-text summary of a check, for the download button."""
    lines = [
        "Symptom Checker Assistant - Report",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Reported symptoms:",
    ]
    lines += [f"  - {human_label(s)}" for s in selected]
    lines += ["", "Top possible conditions (statistical match, not a diagnosis):"]
    lines += [f"  {i+1}. {c}  ({p*100:.1f}%)" for i, (c, p) in enumerate(ranking)]
    lines += [
        "",
        "EDUCATIONAL DEMO ONLY - not medical advice. Trained on synthetic data,",
        "not clinically validated. Consult a qualified doctor for real concerns;",
        "call your local emergency services for anything urgent.",
    ]
    return "\n".join(lines)


def main():
    st.set_page_config(page_title="Symptom Checker Assistant", page_icon="🩺")

    st.title("🩺 Symptom Checker Assistant")
    st.caption("A machine-learning capstone demo project")

    # Persistent warning banner: not medical advice.
    st.warning(
        "⚠️ **Educational demo only - not medical advice.** This app was trained "
        "on synthetic data and is not clinically validated. It cannot diagnose "
        "you. For real health concerns, please consult a qualified doctor; "
        "for anything urgent, call your local emergency services."
    )

    try:
        model, symptom_list = load_model()
    except FileNotFoundError:
        st.error(
            "Model files not found. Run `generate_data.py` then `train_model.py` "
            "before starting the app."
        )
        st.stop()

    if "history" not in st.session_state:
        st.session_state.history = []

    symptom_labels = {s: human_label(s) for s in symptom_list}
    selected = st.multiselect(
        "Which symptoms are you experiencing?",
        options=symptom_list,
        format_func=lambda s: symptom_labels[s],
    )

    check_pressed = st.button(
        "Check possible conditions",
        type="primary",
        disabled=len(selected) == 0,
    )

    if check_pressed:
        # Build the one-hot input row in the exact training column order.
        row = {s: 0 for s in symptom_list}
        for s in selected:
            row[s] = 1
        input_df = pd.DataFrame([row], columns=symptom_list)

        probabilities = model.predict_proba(input_df)[0]
        classes = model.classes_

        ranking = sorted(zip(classes, probabilities), key=lambda x: x[1], reverse=True)
        ranking = ranking[:TOP_N]

        # --- Feature 1: confidence-aware messaging ---
        top_condition, top_prob = ranking[0]
        if top_prob < LOW_CONFIDENCE_THRESHOLD:
            st.warning(
                "🤔 Your selected symptoms don't strongly match any single "
                "condition in the model - the results below are a weak "
                "statistical guess. Try adding more specific symptoms, or "
                "treat this as inconclusive."
            )

        st.subheader("Top possible conditions")

        # --- Feature 2: bar chart comparison alongside the detail list ---
        chart_df = pd.DataFrame(
            {"Condition": [c for c, _ in ranking], "Probability (%)": [p * 100 for _, p in ranking]}
        ).set_index("Condition")
        st.bar_chart(chart_df)

        for condition, prob in ranking:
            percent = prob * 100
            st.markdown(f"**{condition}**")
            st.progress(float(prob), text=f"{percent:.1f}%")

        st.info(
            "These are statistical matches produced by a machine-learning model "
            "on synthetic data - **not a diagnosis**. Only a real doctor can "
            "evaluate your situation."
        )

        # --- Feature 3: downloadable report ---
        report_text = build_report_text(selected, ranking)
        st.download_button(
            "📄 Download this report",
            data=report_text,
            file_name=f"symptom_check_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
            mime="text/plain",
        )

        # --- Feature 4: session check history ---
        st.session_state.history.append(
            {
                "time": datetime.now().strftime("%H:%M:%S"),
                "symptoms": [human_label(s) for s in selected],
                "top_condition": top_condition,
                "top_prob": top_prob,
            }
        )

    # --- Feature 4 (display): session check history ---
    if st.session_state.history:
        with st.sidebar:
            st.subheader("📝 This session's checks")
            for entry in reversed(st.session_state.history):
                st.markdown(
                    f"**{entry['time']}** - {entry['top_condition']} "
                    f"({entry['top_prob']*100:.0f}%)"
                )
                st.caption(", ".join(entry["symptoms"]))
                st.divider()

    # --- Feature 5: model insight / explainability ---
    with st.expander("🔍 How does this model decide?"):
        st.write(
            "This uses a Random Forest classifier. Below are the symptoms it "
            "relies on most heavily across *all* predictions (not just yours) - "
            "useful context for understanding what drives its decisions."
        )
        importances = pd.Series(
            model.feature_importances_, index=symptom_list
        ).sort_values(ascending=False)
        top_importances = importances.head(10)
        importance_df = pd.DataFrame(
            {"Symptom": [human_label(s) for s in top_importances.index],
             "Importance": top_importances.values}
        ).set_index("Symptom")
        st.bar_chart(importance_df)


if __name__ == "__main__":
    main()
