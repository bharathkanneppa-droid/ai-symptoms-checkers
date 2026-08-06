"""Generate a synthetic symptom-disease dataset for the Symptom Checker Assistant.

NOTE: The data produced by this script is SYNTHETIC and programmatically
invented for educational/demo purposes only. It does NOT reflect real
medical statistics and must not be used for any clinical decision.

Swapping in a real dataset (e.g. Kaggle's "Disease Symptom Prediction"
dataset) later only requires matching the same column shape:
one row per patient case, one 0/1 column per symptom, and a final
"condition" column holding the target label.
"""

import random
from pathlib import Path

import pandas as pd

random.seed(42)

# --------------------------------------------------------------------------- #
# Condition definitions
# Each condition lists its "core" symptoms (almost always present) and its
# "optional" symptoms (present only some of the time).
# --------------------------------------------------------------------------- #
CONDITIONS = {
    "Common Cold": {
        "core": ["runny_nose", "sneezing"],
        "optional": ["sore_throat", "cough", "fatigue", "headache", "nasal_congestion"],
    },
    "Influenza (Flu)": {
        "core": ["fever", "body_aches", "fatigue"],
        "optional": ["chills", "headache", "cough", "sore_throat", "runny_nose"],
    },
    "Migraine": {
        "core": ["headache", "nausea"],
        "optional": ["light_sensitivity", "sound_sensitivity", "vomiting", "vision_disturbance", "dizziness"],
    },
    "Allergic Rhinitis": {
        "core": ["sneezing", "itchy_eyes", "runny_nose"],
        "optional": ["watery_eyes", "nasal_congestion", "itchy_throat"],
    },
    "Gastroenteritis": {
        "core": ["nausea", "diarrhea", "abdominal_pain"],
        "optional": ["vomiting", "fever", "headache", "fatigue", "chills"],
    },
    "Sinusitis": {
        "core": ["nasal_congestion", "facial_pain"],
        "optional": ["headache", "runny_nose", "cough", "fever", "fatigue"],
    },
    "Urinary Tract Infection": {
        "core": ["frequent_urination", "burning_on_urination"],
        "optional": ["abdominal_pain", "lower_back_pain", "fever", "blood_in_urine"],
    },
    "Strep Throat": {
        "core": ["sore_throat", "difficulty_swallowing"],
        "optional": ["fever", "headache", "nausea", "chills", "fatigue"],
    },
    "Bronchitis": {
        "core": ["cough", "chest_tightness"],
        "optional": ["fatigue", "fever", "shortness_of_breath", "sore_throat", "wheezing"],
    },
    "Tension Headache": {
        "core": ["headache"],
        "optional": ["neck_stiffness", "fatigue", "dizziness", "light_sensitivity"],
    },
    "Food Poisoning": {
        "core": ["nausea", "vomiting", "diarrhea"],
        "optional": ["abdominal_pain", "fever", "chills", "fatigue", "headache"],
    },
    "Conjunctivitis": {
        "core": ["itchy_eyes", "red_eyes"],
        "optional": ["watery_eyes", "eye_discharge", "light_sensitivity", "swelling_of_eyelids"],
    },
    "Asthma": {
        "core": ["shortness_of_breath", "wheezing"],
        "optional": ["cough", "chest_tightness", "fatigue", "difficulty_sleeping"],
    },
    "Heartburn (GERD)": {
        "core": ["heartburn", "regurgitation"],
        "optional": ["chest_pain", "sour_taste_in_mouth", "difficulty_swallowing", "cough", "nausea"],
    },
    "Menstrual Cramps": {
        "core": ["abdominal_pain", "lower_back_pain"],
        "optional": ["headache", "fatigue", "nausea", "diarrhea"],
    },
    "Constipation": {
        "core": ["hard_stools", "difficulty_passing_stool"],
        "optional": ["abdominal_pain", "bloating", "fatigue"],
    },
    "Insomnia": {
        "core": ["difficulty_sleeping"],
        "optional": ["fatigue", "irritability", "headache", "difficulty_concentrating"],
    },
    "Dehydration": {
        "core": ["fatigue", "dizziness", "dry_mouth"],
        "optional": ["headache", "nausea", "dark_urine", "muscle_cramps"],
    },
    "Ear Infection": {
        "core": ["ear_pain", "ear_pressure"],
        "optional": ["fever", "dizziness", "difficulty_hearing", "headache", "fatigue"],
    },
    "Chickenpox": {
        "core": ["skin_rash", "itching"],
        "optional": ["fever", "fatigue", "headache", "loss_of_appetite"],
    },
}

# --------------------------------------------------------------------------- #
# Generation parameters
# --------------------------------------------------------------------------- #
SAMPLES_PER_CONDITION = 40
OPTIONAL_PROBABILITY = 0.5  # each optional symptom on ~50% of the time
NOISE_PROBABILITY = 0.15    # ~15% chance of one unrelated symptom for noise


def make_symptom_columns():
    """Return the full ordered list of 0/1 symptom columns."""
    symptoms = set()
    for info in CONDITIONS.values():
        symptoms.update(info["core"])
        symptoms.update(info["optional"])
    return sorted(symptoms)


def generate_one_case(condition, symptoms):
    """Build a dict with a 0/1 flag for every symptom plus the label."""
    info = CONDITIONS[condition]
    core, optional = info["core"], info["optional"]

    row = {symptom: 0 for symptom in symptoms}

    # Core symptoms are always on.
    for symptom in core:
        row[symptom] = 1

    # Each optional symptom is on with ~50% probability.
    for symptom in optional:
        if random.random() < OPTIONAL_PROBABILITY:
            row[symptom] = 1

    # A small chance of one random UNRELATED symptom (not core/optional).
    unrelated = [s for s in symptoms if s not in set(core) | set(optional)]
    if unrelated and random.random() < NOISE_PROBABILITY:
        row[random.choice(unrelated)] = 1

    row["condition"] = condition
    return row


def main():
    symptoms = make_symptom_columns()
    rows = []
    for condition in CONDITIONS:
        for _ in range(SAMPLES_PER_CONDITION):
            rows.append(generate_one_case(condition, symptoms))

    df = pd.DataFrame(rows, columns=symptoms + ["condition"])
    # Put the label column last.
    df = df[symptoms + ["condition"]]

    out_path = Path(__file__).resolve().parent / "data" / "symptom_disease.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)

    print(f"Generated {len(df):,} rows x {df.shape[1]} columns")
    print(f"Conditions: {len(CONDITIONS)}")
    print(f"Symptoms: {len(symptoms)}")
    print(f"Saved to: {out_path}")


if __name__ == "__main__":
    main()
