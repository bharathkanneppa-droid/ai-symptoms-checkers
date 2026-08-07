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
LOW_CONFIDENCE_THRESHOLD = 0.30

RED_FLAG_SYMPTOMS = {
    "chest_pain",
    "chest_tightness",
    "shortness_of_breath",
    "difficulty_swallowing",
    "blood_in_urine",
    "wheezing",
    "neck_stiffness",
}

SELF_CARE_GUIDANCE = {
    "Allergic Rhinitis": "Avoid known triggers (pollen, dust, pet dander) when "
        "possible, keep windows closed during high-pollen periods, and rinse "
        "sinuses with saline.",
    "Asthma": "Avoid known triggers (smoke, cold air, allergens) and monitor "
        "your breathing closely. Seek care immediately if breathing worsens "
        "or a rescue inhaler isn't helping.",
    "Bronchitis": "Rest, stay well hydrated, use a humidifier, and avoid smoke "
        "or other lung irritants.",
    "Chickenpox": "Rest, stay hydrated, keep skin clean, avoid scratching, and "
        "avoid contact with others until no longer contagious.",
    "Common Cold": "Rest, drink plenty of fluids, use humidified air, and try "
        "warm salt-water gargles for a sore throat.",
    "Conjunctivitis": "Avoid touching or rubbing your eyes, wash hands "
        "frequently, use clean warm compresses, and don't share towels or "
        "pillows.",
    "Constipation": "Increase fiber and fluid intake, stay physically active, "
        "and try to keep a regular bathroom routine.",
    "Dehydration": "Increase fluid intake steadily, rest in a cool "
        "environment, and avoid alcohol or caffeine until you feel better.",
    "Ear Infection": "Rest, a warm compress against the ear may help with "
        "discomfort, and avoid inserting anything into the ear.",
    "Food Poisoning": "Stay hydrated with small, frequent sips of fluids, "
        "rest, and ease back into eating with bland foods.",
    "Gastroenteritis": "Stay hydrated, rest, and ease back into eating with "
        "bland foods (rice, toast, bananas) - avoid dairy and greasy food "
        "for a bit.",
    "Heartburn (GERD)": "Avoid large or late meals, steer clear of known "
        "trigger foods (spicy, fatty, caffeine, alcohol), and stay upright "
        "after eating.",
    "Influenza (Flu)": "Rest, stay hydrated, monitor your temperature, and "
        "avoid close contact with others while contagious.",
    "Insomnia": "Keep a consistent sleep schedule, limit screens before bed, "
        "avoid late caffeine, and keep the bedroom cool and dark.",
    "Menstrual Cramps": "Rest, a warm compress on the lower abdomen can help, "
        "gentle movement or stretching, and stay hydrated.",
    "Migraine": "Rest in a dark, quiet room, stay hydrated, try a cool "
        "compress, and note any potential triggers for next time.",
    "Sinusitis": "Use a humidifier, try saline nasal rinses, stay hydrated, "
        "and apply warm compresses to the face.",
    "Strep Throat": "Rest, stay hydrated, and gargle warm salt water - this "
        "one is often bacterial, so a doctor's evaluation matters more than "
        "usual here.",
    "Tension Headache": "Rest, stay hydrated, manage stress where you can, "
        "and try a warm or cool compress on the neck and shoulders.",
    "Urinary Tract Infection": "Stay well hydrated and don't hold urine for "
        "long periods - UTIs often need professional treatment, so a doctor "
        "visit is a good idea.",
}

SYMPTOM_LABELS = {
    "runny_nose": "Runny nose", "sneezing": "Sneezing", "sore_throat": "Sore throat",
    "cough": "Cough", "headache": "Headache", "fever": "Fever", "fatigue": "Fatigue",
    "nasal_congestion": "Nasal congestion", "body_aches": "Body aches", "chills": "Chills",
    "nausea": "Nausea", "vomiting": "Vomiting", "diarrhea": "Diarrhea",
    "abdominal_pain": "Abdominal pain", "watery_eyes": "Watery eyes", "itchy_eyes": "Itchy eyes",
    "skin_rash": "Skin rash", "frequent_urination": "Frequent urination",
    "burning_on_urination": "Burning on urination", "lower_back_pain": "Lower back pain",
    "dizziness": "Dizziness", "shortness_of_breath": "Shortness of breath",
    "chest_tightness": "Chest tightness", "loss_of_appetite": "Loss of appetite",
    "light_sensitivity": "Light sensitivity", "sound_sensitivity": "Sound sensitivity",
    "vision_disturbance": "Vision disturbance", "itchy_throat": "Itchy throat",
    "facial_pain": "Facial pain", "blood_in_urine": "Blood in urine",
    "difficulty_swallowing": "Difficulty swallowing", "wheezing": "Wheezing",
    "neck_stiffness": "Neck stiffness", "red_eyes": "Red eyes", "eye_discharge": "Eye discharge",
    "swelling_of_eyelids": "Swollen eyelids", "heartburn": "Heartburn",
    "regurgitation": "Regurgitation", "chest_pain": "Chest pain",
    "sour_taste_in_mouth": "Sour taste in mouth", "difficulty_sleeping": "Difficulty sleeping",
    "hard_stools": "Hard stools", "difficulty_passing_stool": "Difficulty passing stool",
    "bloating": "Bloating", "irritability": "Irritability",
    "difficulty_concentrating": "Difficulty concentrating", "dry_mouth": "Dry mouth",
    "dark_urine": "Dark urine", "muscle_cramps": "Muscle cramps", "ear_pain": "Ear pain",
    "ear_pressure": "Ear pressure", "difficulty_hearing": "Difficulty hearing",
    "itching": "Itching",
}

# Phrases used for simple keyword matching in the chat tab. Rule-based, not a
# language model - deliberately transparent about that in the UI.
SYMPTOM_KEYWORDS = {
    "runny_nose": ["runny nose", "nose is running", "nose keeps running"],
    "sneezing": ["sneezing", "sneeze", "sneezes"],
    "sore_throat": ["sore throat", "throat hurts", "throat pain", "throat is sore"],
    "cough": ["cough", "coughing"],
    "headache": ["headache", "head hurts", "head pain", "head is pounding"],
    "fever": ["fever", "high temperature", "running a temperature"],
    "fatigue": ["fatigue", "tired", "exhausted", "no energy", "worn out"],
    "nasal_congestion": ["stuffy nose", "nasal congestion", "blocked nose", "congested nose"],
    "body_aches": ["body aches", "body ache", "aching all over", "muscles ache"],
    "chills": ["chills", "shivering", "cold and shaky"],
    "nausea": ["nausea", "nauseous", "feel sick", "queasy"],
    "vomiting": ["vomit", "vomiting", "throwing up", "threw up"],
    "diarrhea": ["diarrhea", "loose stools", "watery stools"],
    "abdominal_pain": ["stomach pain", "stomach ache", "abdominal pain", "belly pain", "tummy hurts"],
    "watery_eyes": ["watery eyes", "eyes watering", "teary eyes"],
    "itchy_eyes": ["itchy eyes", "eyes are itchy", "eyes itch"],
    "skin_rash": ["rash", "skin rash", "red spots on skin"],
    "frequent_urination": ["peeing a lot", "frequent urination", "urinating a lot", "bathroom often"],
    "burning_on_urination": ["burning when i pee", "burning urination", "pain when urinating", "burns when i pee"],
    "lower_back_pain": ["lower back pain", "back pain", "lower back hurts"],
    "dizziness": ["dizzy", "dizziness", "lightheaded", "feel faint"],
    "shortness_of_breath": ["short of breath", "shortness of breath", "can't breathe", "cant breathe", "breathless", "trouble breathing", "difficulty breathing"],
    "chest_tightness": ["chest tightness", "chest feels tight", "tightness in chest"],
    "loss_of_appetite": ["no appetite", "loss of appetite", "not hungry", "don't feel like eating"],
    "light_sensitivity": ["sensitive to light", "light hurts my eyes", "light sensitivity"],
    "sound_sensitivity": ["sensitive to sound", "noise hurts", "sound sensitivity", "loud noises bother me"],
    "vision_disturbance": ["blurry vision", "vision disturbance", "trouble seeing", "vision is off"],
    "itchy_throat": ["itchy throat", "throat is itchy", "throat itches"],
    "facial_pain": ["facial pain", "face hurts", "pain in my face"],
    "blood_in_urine": ["blood in urine", "blood in my pee", "urine looks bloody"],
    "difficulty_swallowing": ["trouble swallowing", "difficulty swallowing", "hard to swallow", "can't swallow", "cant swallow"],
    "wheezing": ["wheezing", "wheeze", "whistling sound when breathing"],
    "neck_stiffness": ["stiff neck", "neck stiffness", "neck feels stiff", "can't move my neck"],
    "red_eyes": ["red eyes", "eyes are red", "bloodshot eyes"],
    "eye_discharge": ["eye discharge", "eyes are crusty", "discharge from eyes", "gunk in eyes"],
    "swelling_of_eyelids": ["swollen eyelids", "eyelids are swollen", "puffy eyelids"],
    "heartburn": ["heartburn", "burning in chest after eating", "acid reflux"],
    "regurgitation": ["regurgitation", "food coming back up", "acid coming up"],
    "chest_pain": ["chest pain", "chest hurts", "pain in my chest"],
    "sour_taste_in_mouth": ["sour taste", "bad taste in mouth"],
    "difficulty_sleeping": ["can't sleep", "cant sleep", "trouble sleeping", "difficulty sleeping", "insomnia"],
    "hard_stools": ["hard stools", "stools are hard"],
    "difficulty_passing_stool": ["difficulty passing stool", "can't poop", "cant poop", "trouble pooping", "constipated"],
    "bloating": ["bloating", "bloated", "stomach feels bloated"],
    "irritability": ["irritable", "irritability", "easily annoyed", "short tempered"],
    "difficulty_concentrating": ["can't concentrate", "cant concentrate", "trouble concentrating", "difficulty concentrating", "can't focus"],
    "dry_mouth": ["dry mouth", "mouth feels dry"],
    "dark_urine": ["dark urine", "urine is dark", "pee is dark"],
    "muscle_cramps": ["muscle cramps", "cramping muscles", "leg cramps"],
    "ear_pain": ["ear pain", "ear hurts", "pain in my ear"],
    "ear_pressure": ["ear pressure", "ears feel full", "pressure in ears"],
    "difficulty_hearing": ["difficulty hearing", "trouble hearing", "can't hear well", "hearing loss"],
    "itching": ["itching", "itchy skin", "i'm itchy", "im itchy"],
}

DONE_TRIGGERS = [
    "done", "that's all", "thats all", "that's it", "thats it", "finished",
    "that should be everything", "nothing else", "no more symptoms",
    "check now", "diagnose", "that is all",
]
RESET_TRIGGERS = ["reset", "start over", "restart"]


@st.cache_resource
def load_model():
    model = joblib.load(MODEL_PATH)
    symptom_list = joblib.load(SYMPTOM_LIST_PATH)
    return model, symptom_list


def human_label(symptom):
    return SYMPTOM_LABELS.get(symptom, symptom.replace("_", " ").title())


def extract_symptoms_from_text(text):
    """Very simple rule-based keyword matching against a fixed vocabulary."""
    text_lower = text.lower()
    found = set()
    for symptom, phrases in SYMPTOM_KEYWORDS.items():
        if any(phrase in text_lower for phrase in phrases):
            found.add(symptom)
    return found


def build_report_text(selected, ranking):
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


def compute_ranking(selected, model, symptom_list):
    """Pure computation: no rendering, no session-state side effects."""
    flags = [s for s in selected if s in RED_FLAG_SYMPTOMS]
    row = {s: 0 for s in symptom_list}
    for s in selected:
        row[s] = 1
    input_df = pd.DataFrame([row], columns=symptom_list)
    probabilities = model.predict_proba(input_df)[0]
    classes = model.classes_
    ranking = sorted(zip(classes, probabilities), key=lambda x: x[1], reverse=True)[:TOP_N]
    return ranking, flags


def record_history(selected, ranking):
    top_condition, top_prob = ranking[0]
    st.session_state.history.append(
        {
            "time": datetime.now().strftime("%H:%M:%S"),
            "symptoms": [human_label(s) for s in selected],
            "top_condition": top_condition,
            "top_prob": top_prob,
        }
    )


def render_ranking(selected, ranking, flags, key_suffix):
    """Pure rendering: safe to call every rerun, including chat history replay."""
    if flags:
        flag_labels = ", ".join(human_label(s) for s in flags)
        st.error(
            f"🚨 **{flag_labels}** can indicate a medical emergency. "
            "Please seek immediate medical attention or contact your local "
            "emergency services. This app is not designed to assess urgent "
            "symptoms safely, so please don't rely on it here."
        )

    top_condition, top_prob = ranking[0]
    if top_prob < LOW_CONFIDENCE_THRESHOLD:
        st.warning(
            "🤔 Your selected symptoms don't strongly match any single "
            "condition in the model - the results below are a weak "
            "statistical guess. Try adding more specific symptoms, or "
            "treat this as inconclusive."
        )

    st.subheader("Top possible conditions")
    chart_df = pd.DataFrame(
        {"Condition": [c for c, _ in ranking], "Probability (%)": [p * 100 for _, p in ranking]}
    ).set_index("Condition")
    st.bar_chart(chart_df)

    for condition, prob in ranking:
        percent = prob * 100
        st.markdown(f"**{condition}**")
        st.progress(float(prob), text=f"{percent:.1f}%")

    guidance = SELF_CARE_GUIDANCE.get(top_condition)
    if guidance and not flags:
        st.subheader("General self-care information")
        st.markdown(guidance)
        st.caption(
            "General lifestyle guidance only - not treatment, not a "
            "prescription. See a doctor if symptoms persist beyond a few "
            "days, worsen, or you develop a high fever or severe pain."
        )

    st.info(
        "These are statistical matches produced by a machine-learning model "
        "on synthetic data - **not a diagnosis**. Only a real doctor can "
        "evaluate your situation."
    )

    report_text = build_report_text(selected, ranking)
    st.download_button(
        "📄 Download this report",
        data=report_text,
        file_name=f"symptom_check_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
        mime="text/plain",
        key=f"download_{key_suffix}",
    )


def render_checklist_tab(model, symptom_list):
    symptom_labels = {s: human_label(s) for s in symptom_list}
    selected = st.multiselect(
        "Which symptoms are you experiencing?",
        options=symptom_list,
        format_func=lambda s: symptom_labels[s],
    )

    check_pressed = st.button(
        "Check possible conditions", type="primary", disabled=len(selected) == 0
    )

    if check_pressed:
        ranking, flags = compute_ranking(selected, model, symptom_list)
        record_history(selected, ranking)
        render_ranking(selected, ranking, flags, key_suffix="checklist")


def render_chat_tab(model, symptom_list):
    st.caption(
        "This chat recognizes common symptom phrases from a fixed vocabulary - "
        "it's a rule-based front end to the same model above, not a general "
        "AI. Describe how you're feeling, and type **\"done\"** when finished."
    )

    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "type": "text",
                "content": (
                    "Hi, I'm your Symptom Checker Assistant 🩺 - not a real "
                    "doctor, but I can help point toward possible directions "
                    "to look into. Tell me what's going on today, in your "
                    "own words."
                ),
            }
        ]
    if "chat_symptoms" not in st.session_state:
        st.session_state.chat_symptoms = set()

    for idx, msg in enumerate(st.session_state.chat_messages):
        with st.chat_message(msg["role"]):
            if msg["type"] == "text":
                st.markdown(msg["content"])
            elif msg["type"] == "diagnosis":
                render_ranking(
                    msg["selected"], msg["ranking"], msg["flags"], key_suffix=f"chat{idx}"
                )

    prompt = st.chat_input("Tell me what you're feeling...")
    if prompt:
        st.session_state.chat_messages.append({"role": "user", "type": "text", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        text_lower = prompt.strip().lower()

        if any(t in text_lower for t in RESET_TRIGGERS):
            st.session_state.chat_symptoms = set()
            reply = "Okay, I've cleared what you've told me so far. What's bothering you?"
            st.session_state.chat_messages.append({"role": "assistant", "type": "text", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)

        elif any(t in text_lower for t in DONE_TRIGGERS):
            if not st.session_state.chat_symptoms:
                reply = (
                    "I haven't picked up on any symptoms yet - could you "
                    "describe what you're feeling first?"
                )
                st.session_state.chat_messages.append({"role": "assistant", "type": "text", "content": reply})
                with st.chat_message("assistant"):
                    st.markdown(reply)
            else:
                selected = sorted(st.session_state.chat_symptoms)
                ranking, flags = compute_ranking(selected, model, symptom_list)
                record_history(selected, ranking)
                msg_idx = len(st.session_state.chat_messages)
                st.session_state.chat_messages.append(
                    {"role": "assistant", "type": "diagnosis", "selected": selected, "ranking": ranking, "flags": flags}
                )
                with st.chat_message("assistant"):
                    render_ranking(selected, ranking, flags, key_suffix=f"chat{msg_idx}")
                st.session_state.chat_symptoms = set()

        else:
            newly_found = extract_symptoms_from_text(prompt)
            st.session_state.chat_symptoms |= newly_found
            flags_now = [s for s in newly_found if s in RED_FLAG_SYMPTOMS]
            non_flag_new = [s for s in newly_found if s not in RED_FLAG_SYMPTOMS]

            reply_parts = []
            if flags_now:
                flag_labels = ", ".join(human_label(s) for s in flags_now)
                reply_parts.append(
                    f"🚨 **{flag_labels}** can indicate a medical emergency - "
                    "please seek immediate medical attention or contact "
                    "emergency services. I've noted it, but please don't "
                    "wait on this app for anything urgent."
                )
            if non_flag_new:
                noted = ", ".join(human_label(s) for s in non_flag_new)
                reply_parts.append(f"Noted: **{noted}**.")
            if newly_found:
                all_so_far = ", ".join(human_label(s) for s in sorted(st.session_state.chat_symptoms))
                reply_parts.append(
                    f"So far I have: {all_so_far}. Tell me more, or type "
                    "**\"done\"** when you're ready for me to check possible conditions."
                )
            if not newly_found:
                reply_parts.append(
                    "I didn't catch a specific symptom in that. Try "
                    "describing it plainly, e.g. \"I have a headache and "
                    "sore throat,\" or type **\"done\"** if you're finished."
                )
            reply = "\n\n".join(reply_parts)
            st.session_state.chat_messages.append({"role": "assistant", "type": "text", "content": reply})
            with st.chat_message("assistant"):
                st.markdown(reply)


def main():
    st.set_page_config(page_title="Symptom Checker Assistant", page_icon="🩺")

    st.title("🩺 Symptom Checker Assistant")
    st.caption("A machine-learning capstone demo project")

    st.warning(
        "⚠️ **Educational demo only - not medical advice.** This app was trained "
        "on synthetic data and is not clinically validated. It cannot diagnose "
        "you, and it does not provide medication or treatment guidance. For "
        "real health concerns, please consult a qualified doctor; for anything "
        "urgent, call your local emergency services."
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

    tab1, tab2 = st.tabs(["📋 Symptom Checklist", "💬 Chat with Assistant"])
    with tab1:
        render_checklist_tab(model, symptom_list)
    with tab2:
        render_chat_tab(model, symptom_list)

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
