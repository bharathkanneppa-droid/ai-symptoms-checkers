"""Knowledge base for the AI Doctor chat.

Two things live here:

1. ``SYMPTOMS`` - metadata for every symptom the RandomForest model was
   trained on (friendly label, natural-language aliases, and the question the
   bot asks when probing for it).

2. ``CONDITIONS`` - the 20 conditions from data/symptom_disease.csv with their
   core/optional symptoms (mirrors generate_data.py) plus non-model metadata
   such as recommended specialist, department, severity and self-care advice.

All of it is for educational use only. Nothing here is clinical advice.
"""

# --------------------------------------------------------------------------- #
# Symptom metadata
# --------------------------------------------------------------------------- #
SYMPTOMS = {
    "abdominal_pain": {
        "label": "Abdominal pain",
        "aliases": ["abdominal pain", "stomach ache", "stomach pain", "belly pain", "tummy ache", "cramps in stomach"],
        "question": "Are you experiencing any abdominal or stomach pain?",
    },
    "bloating": {
        "label": "Bloating",
        "aliases": ["bloating", "bloated", "gas", "fullness"],
        "question": "Do you feel bloated or have gas?",
    },
    "blood_in_urine": {
        "label": "Blood in urine",
        "aliases": ["blood in urine", "bloody urine", "blood when urinating"],
        "question": "Have you noticed any blood in your urine?",
    },
    "body_aches": {
        "label": "Body aches",
        "aliases": ["body ache", "body aches", "muscle pain", "aching body", "body pain", "muscle ache"],
        "question": "Are you experiencing any body aches or muscle pain?",
    },
    "burning_on_urination": {
        "label": "Burning on urination",
        "aliases": ["burning urination", "burning when urinating", "pain when urinating", "burning pee", "burning while peeing", "painful urination"],
        "question": "Do you feel burning or pain when you urinate?",
    },
    "chest_pain": {
        "label": "Chest pain",
        "aliases": ["chest pain", "pain in chest", "chest discomfort", "chest hurt"],
        "question": "Are you experiencing any chest pain?",
    },
    "chest_tightness": {
        "label": "Chest tightness",
        "aliases": ["chest tightness", "tight chest", "pressure in chest", "chest pressure"],
        "question": "Do you feel tightness or pressure in your chest?",
    },
    "chills": {
        "label": "Chills",
        "aliases": ["chills", "shivering", "shivers", "cold shivers", "feeling cold"],
        "question": "Do you have chills or shivering?",
    },
    "cough": {
        "label": "Cough",
        "aliases": ["cough", "coughing", "dry cough", "wet cough", "persistent cough", "coughing a lot"],
        "question": "Do you have a cough?",
    },
    "dark_urine": {
        "label": "Dark urine",
        "aliases": ["dark urine", "dark pee", "dark colored urine", "dark yellow urine"],
        "question": "Is your urine darker than usual?",
    },
    "diarrhea": {
        "label": "Diarrhea",
        "aliases": ["diarrhea", "loose stools", "loose motions", "frequent stools", "watery stool", "running stomach"],
        "question": "Are you having diarrhea or loose stools?",
    },
    "difficulty_concentrating": {
        "label": "Difficulty concentrating",
        "aliases": ["difficulty concentrating", "can't focus", "trouble focusing", "foggy brain", "brain fog"],
        "question": "Have you had trouble concentrating?",
    },
    "difficulty_hearing": {
        "label": "Difficulty hearing",
        "aliases": ["difficulty hearing", "hearing loss", "muffled hearing", "can't hear well"],
        "question": "Do you have any difficulty hearing?",
    },
    "difficulty_passing_stool": {
        "label": "Difficulty passing stool",
        "aliases": ["difficulty passing stool", "constipated", "hard to pass stool", "straining", "can't pass stool"],
        "question": "Do you have difficulty passing stool?",
    },
    "difficulty_sleeping": {
        "label": "Difficulty sleeping",
        "aliases": ["difficulty sleeping", "can't sleep", "insomnia", "trouble sleeping", "sleep problems", "not sleeping"],
        "question": "Are you having difficulty sleeping?",
    },
    "difficulty_swallowing": {
        "label": "Difficulty swallowing",
        "aliases": ["difficulty swallowing", "pain swallowing", "hard to swallow", "trouble swallowing", "can't swallow"],
        "question": "Do you have difficulty swallowing?",
    },
    "dizziness": {
        "label": "Dizziness",
        "aliases": ["dizziness", "dizzy", "light headed", "lightheaded", "feeling faint", "vertigo", "spinning"],
        "question": "Do you feel dizzy or lightheaded?",
    },
    "dry_mouth": {
        "label": "Dry mouth",
        "aliases": ["dry mouth", "dry throat", "mouth dryness", "parched mouth"],
        "question": "Does your mouth feel dry?",
    },
    "ear_pain": {
        "label": "Ear pain",
        "aliases": ["ear pain", "earache", "pain in ear", "ear ache", "ear hurt"],
        "question": "Are you experiencing any ear pain?",
    },
    "ear_pressure": {
        "label": "Ear pressure",
        "aliases": ["ear pressure", "fullness in ear", "blocked ear", "ear feels full", "plugged ear"],
        "question": "Do you feel pressure or fullness in your ears?",
    },
    "eye_discharge": {
        "label": "Eye discharge",
        "aliases": ["eye discharge", "discharge from eye", "eye crust", "pus in eye", "sticky eye"],
        "question": "Is there any discharge from your eyes?",
    },
    "facial_pain": {
        "label": "Facial pain",
        "aliases": ["facial pain", "face pain", "pain in face", "sinus pain", "face pressure"],
        "question": "Are you experiencing any pain around your face?",
    },
    "fatigue": {
        "label": "Fatigue",
        "aliases": ["fatigue", "tired", "tiredness", "exhausted", "weak", "no energy", "lethargic", "drained"],
        "question": "Do you feel unusually tired or fatigued?",
    },
    "fever": {
        "label": "Fever",
        "aliases": ["fever", "high temperature", "temperature", "feverish", "hot body", "pyrexia", "running temperature"],
        "question": "Do you have a fever?",
    },
    "frequent_urination": {
        "label": "Frequent urination",
        "aliases": ["frequent urination", "urinating often", "pee often", "frequent peeing", "urinate a lot"],
        "question": "Are you urinating more often than usual?",
    },
    "hard_stools": {
        "label": "Hard stools",
        "aliases": ["hard stools", "hard stool", "hard poop", "dry stool"],
        "question": "Are your stools hard or dry?",
    },
    "headache": {
        "label": "Headache",
        "aliases": ["headache", "head ache", "head pain", "pain in head", "head hurting", "migraine", "head throbbing"],
        "question": "Do you have a headache?",
    },
    "heartburn": {
        "label": "Heartburn",
        "aliases": ["heartburn", "acid reflux", "burning chest", "burning sensation", "acidity"],
        "question": "Are you experiencing heartburn or a burning feeling?",
    },
    "irritability": {
        "label": "Irritability",
        "aliases": ["irritability", "irritable", "easily annoyed", "irritated", "short tempered", "frustrated easily"],
        "question": "Have you been feeling irritable lately?",
    },
    "itching": {
        "label": "Itching",
        "aliases": ["itching", "itchy skin", "itch", "skin itching", "scratchy skin"],
        "question": "Do you have any itching or itchy skin?",
    },
    "itchy_eyes": {
        "label": "Itchy eyes",
        "aliases": ["itchy eyes", "itching eyes", "eyes itch"],
        "question": "Are your eyes itchy?",
    },
    "itchy_throat": {
        "label": "Itchy throat",
        "aliases": ["itchy throat", "scratchy throat", "throat itching"],
        "question": "Does your throat feel itchy or scratchy?",
    },
    "light_sensitivity": {
        "label": "Sensitivity to light",
        "aliases": ["light sensitivity", "sensitive to light", "photophobia", "bothered by light"],
        "question": "Are you sensitive to light?",
    },
    "loss_of_appetite": {
        "label": "Loss of appetite",
        "aliases": ["loss of appetite", "no appetite", "not hungry", "don't feel like eating"],
        "question": "Have you lost your appetite?",
    },
    "lower_back_pain": {
        "label": "Lower back pain",
        "aliases": ["lower back pain", "back pain", "pain in back", "lower back ache", "backache"],
        "question": "Are you experiencing lower back pain?",
    },
    "muscle_cramps": {
        "label": "Muscle cramps",
        "aliases": ["muscle cramps", "cramps", "leg cramps", "muscle spasms", "charley horse"],
        "question": "Do you have any muscle cramps?",
    },
    "nasal_congestion": {
        "label": "Nasal congestion",
        "aliases": ["nasal congestion", "stuffy nose", "blocked nose", "congested nose", "runny congestion"],
        "question": "Do you have nasal congestion or a stuffy nose?",
    },
    "nausea": {
        "label": "Nausea",
        "aliases": ["nausea", "nauseous", "feel sick", "queasy", "sick to my stomach", "want to vomit"],
        "question": "Do you feel nauseous?",
    },
    "neck_stiffness": {
        "label": "Neck stiffness",
        "aliases": ["neck stiffness", "stiff neck", "neck pain", "tight neck"],
        "question": "Do you have a stiff or painful neck?",
    },
    "red_eyes": {
        "label": "Red eyes",
        "aliases": ["red eyes", "bloodshot eyes", "red eye", "pink eye"],
        "question": "Are your eyes red or bloodshot?",
    },
    "regurgitation": {
        "label": "Regurgitation",
        "aliases": ["regurgitation", "acid coming up", "food coming back up", "sour stomach coming up"],
        "question": "Do you experience food or acid coming back up?",
    },
    "runny_nose": {
        "label": "Runny nose",
        "aliases": ["runny nose", "running nose", "nasal discharge", "drippy nose", "sniffles"],
        "question": "Do you have a runny nose?",
    },
    "shortness_of_breath": {
        "label": "Shortness of breath",
        "aliases": ["shortness of breath", "difficulty breathing", "breathless", "can't breathe", "hard to breathe", "out of breath", "struggling to breathe"],
        "question": "Are you experiencing shortness of breath?",
    },
    "skin_rash": {
        "label": "Skin rash",
        "aliases": ["skin rash", "rash", "rash on skin", "red spots", "bumps on skin", "skin breakout"],
        "question": "Do you have a skin rash?",
    },
    "sneezing": {
        "label": "Sneezing",
        "aliases": ["sneezing", "sneeze", "sneezing a lot"],
        "question": "Are you sneezing a lot?",
    },
    "sore_throat": {
        "label": "Sore throat",
        "aliases": ["sore throat", "throat pain", "painful throat", "throat ache", "sore throat pain"],
        "question": "Do you have a sore throat?",
    },
    "sound_sensitivity": {
        "label": "Sensitivity to sound",
        "aliases": ["sound sensitivity", "sensitive to sound", "bothered by noise", "loud sounds bother"],
        "question": "Are you sensitive to sound or noise?",
    },
    "sour_taste_in_mouth": {
        "label": "Sour taste in mouth",
        "aliases": ["sour taste", "sour taste in mouth", "acid taste", "bitter taste in mouth"],
        "question": "Do you have a sour or bitter taste in your mouth?",
    },
    "swelling_of_eyelids": {
        "label": "Swelling of eyelids",
        "aliases": ["swollen eyelids", "swelling of eyelids", "puffy eyelids", "swollen eyes"],
        "question": "Are your eyelids swollen?",
    },
    "vision_disturbance": {
        "label": "Vision disturbance",
        "aliases": ["vision disturbance", "blurred vision", "blurry vision", "visual disturbance", "flashing lights", "vision problems"],
        "question": "Have you noticed any vision disturbance?",
    },
    "vomiting": {
        "label": "Vomiting",
        "aliases": ["vomiting", "vomit", "throwing up", "threw up", "puking", "vomitted"],
        "question": "Have you been vomiting?",
    },
    "watery_eyes": {
        "label": "Watery eyes",
        "aliases": ["watery eyes", "eyes watering", "teary eyes", "watery eyes crying"],
        "question": "Are your eyes watering?",
    },
    "wheezing": {
        "label": "Wheezing",
        "aliases": ["wheezing", "wheeze", "whistling breath", "whistling when breathing"],
        "question": "Are you wheezing or hearing a whistling sound when you breathe?",
    },
}

# --------------------------------------------------------------------------- #
# Condition metadata (mirrors generate_data.py + clinical guidance for the bot)
# --------------------------------------------------------------------------- #
CONDITIONS = {
    "Common Cold": {
        "core": ["runny_nose", "sneezing"],
        "optional": ["sore_throat", "cough", "fatigue", "headache", "nasal_congestion"],
        "specialist": "General Physician",
        "department": "General Medicine",
        "severity": "mild",
        "emergency": False,
        "advice": "Rest, stay hydrated and use saline drops for congestion. See a doctor if symptoms worsen or last more than 10 days.",
    },
    "Influenza (Flu)": {
        "core": ["fever", "body_aches", "fatigue"],
        "optional": ["chills", "headache", "cough", "sore_throat", "runny_nose"],
        "specialist": "General Physician",
        "department": "General Medicine",
        "severity": "moderate",
        "emergency": False,
        "advice": "Rest, fluids and fever reducers help. Consult a doctor, especially if you belong to a high-risk group.",
    },
    "Migraine": {
        "core": ["headache", "nausea"],
        "optional": ["light_sensitivity", "sound_sensitivity", "vomiting", "vision_disturbance", "dizziness"],
        "specialist": "Neurologist",
        "department": "Neurology",
        "severity": "moderate",
        "emergency": False,
        "advice": "Rest in a quiet, dark room and stay hydrated. A neurologist can help plan prevention.",
    },
    "Allergic Rhinitis": {
        "core": ["sneezing", "itchy_eyes", "runny_nose"],
        "optional": ["watery_eyes", "nasal_congestion", "itchy_throat"],
        "specialist": "ENT Specialist",
        "department": "ENT",
        "severity": "mild",
        "emergency": False,
        "advice": "Avoid known allergens and consider an antihistamine. An ENT can confirm triggers.",
    },
    "Gastroenteritis": {
        "core": ["nausea", "diarrhea", "abdominal_pain"],
        "optional": ["vomiting", "fever", "headache", "fatigue", "chills"],
        "specialist": "Gastroenterologist",
        "department": "Gastroenterology",
        "severity": "moderate",
        "emergency": False,
        "advice": "Stay hydrated with oral rehydration salts. See a doctor if you cannot keep fluids down.",
    },
    "Sinusitis": {
        "core": ["nasal_congestion", "facial_pain"],
        "optional": ["headache", "runny_nose", "cough", "fever", "fatigue"],
        "specialist": "ENT Specialist",
        "department": "ENT",
        "severity": "moderate",
        "emergency": False,
        "advice": "Steam inhalation and saline rinses may help. An ENT can assess if antibiotics are needed.",
    },
    "Urinary Tract Infection": {
        "core": ["frequent_urination", "burning_on_urination"],
        "optional": ["abdominal_pain", "lower_back_pain", "fever", "blood_in_urine"],
        "specialist": "Urologist",
        "department": "Urology",
        "severity": "moderate",
        "emergency": False,
        "advice": "Drink plenty of water and consult a doctor - UTIs usually need antibiotics.",
    },
    "Strep Throat": {
        "core": ["sore_throat", "difficulty_swallowing"],
        "optional": ["fever", "headache", "nausea", "chills", "fatigue"],
        "specialist": "ENT Specialist",
        "department": "ENT",
        "severity": "moderate",
        "emergency": False,
        "advice": "See a doctor for a throat swab - strep throat needs antibiotics.",
    },
    "Bronchitis": {
        "core": ["cough", "chest_tightness"],
        "optional": ["fatigue", "fever", "shortness_of_breath", "sore_throat", "wheezing"],
        "specialist": "Pulmonologist",
        "department": "Pulmonology",
        "severity": "moderate",
        "emergency": False,
        "advice": "Rest, fluids and avoiding smoke help. See a doctor if breathing is difficult.",
    },
    "Tension Headache": {
        "core": ["headache"],
        "optional": ["neck_stiffness", "fatigue", "dizziness", "light_sensitivity"],
        "specialist": "Neurologist",
        "department": "Neurology",
        "severity": "mild",
        "emergency": False,
        "advice": "Rest, hydration and relaxation techniques usually help. See a doctor if frequent.",
    },
    "Food Poisoning": {
        "core": ["nausea", "vomiting", "diarrhea"],
        "optional": ["abdominal_pain", "fever", "chills", "fatigue", "headache"],
        "specialist": "Gastroenterologist",
        "department": "Gastroenterology",
        "severity": "moderate",
        "emergency": False,
        "advice": "Stay hydrated. Seek urgent care for severe vomiting or signs of dehydration.",
    },
    "Conjunctivitis": {
        "core": ["itchy_eyes", "red_eyes"],
        "optional": ["watery_eyes", "eye_discharge", "light_sensitivity", "swelling_of_eyelids"],
        "specialist": "Ophthalmologist",
        "department": "Ophthalmology",
        "severity": "mild",
        "emergency": False,
        "advice": "Avoid touching your eyes and wash hands often. An eye exam can rule out infection.",
    },
    "Asthma": {
        "core": ["shortness_of_breath", "wheezing"],
        "optional": ["cough", "chest_tightness", "fatigue", "difficulty_sleeping"],
        "specialist": "Pulmonologist",
        "department": "Pulmonology",
        "severity": "moderate",
        "emergency": True,
        "advice": "Use your reliever inhaler if prescribed. Seek emergency care if breathing worsens rapidly.",
    },
    "Heartburn (GERD)": {
        "core": ["heartburn", "regurgitation"],
        "optional": ["chest_pain", "sour_taste_in_mouth", "difficulty_swallowing", "cough", "nausea"],
        "specialist": "Gastroenterologist",
        "department": "Gastroenterology",
        "severity": "mild",
        "emergency": False,
        "advice": "Avoid heavy meals and lying down after eating. A gastroenterologist can advise on management.",
    },
    "Menstrual Cramps": {
        "core": ["abdominal_pain", "lower_back_pain"],
        "optional": ["headache", "fatigue", "nausea", "diarrhea"],
        "specialist": "Gynecologist",
        "department": "Gynecology",
        "severity": "mild",
        "emergency": False,
        "advice": "Heat packs and rest help. See a gynecologist if pain is severe or persistent.",
    },
    "Constipation": {
        "core": ["hard_stools", "difficulty_passing_stool"],
        "optional": ["abdominal_pain", "bloating", "fatigue"],
        "specialist": "Gastroenterologist",
        "department": "Gastroenterology",
        "severity": "mild",
        "emergency": False,
        "advice": "Increase fiber and water intake. See a doctor if it persists.",
    },
    "Insomnia": {
        "core": ["difficulty_sleeping"],
        "optional": ["fatigue", "irritability", "headache", "difficulty_concentrating"],
        "specialist": "Neurologist",
        "department": "Neurology",
        "severity": "mild",
        "emergency": False,
        "advice": "Maintain a regular sleep schedule and limit screens before bed. A specialist can help.",
    },
    "Dehydration": {
        "core": ["fatigue", "dizziness", "dry_mouth"],
        "optional": ["headache", "nausea", "dark_urine", "muscle_cramps"],
        "specialist": "General Physician",
        "department": "General Medicine",
        "severity": "moderate",
        "emergency": True,
        "advice": "Rehydrate with water or ORS. Seek urgent care if confused, very weak or unable to drink.",
    },
    "Ear Infection": {
        "core": ["ear_pain", "ear_pressure"],
        "optional": ["fever", "dizziness", "difficulty_hearing", "headache", "fatigue"],
        "specialist": "ENT Specialist",
        "department": "ENT",
        "severity": "moderate",
        "emergency": False,
        "advice": "Pain relief can help while waiting. See an ENT doctor for an assessment.",
    },
    "Chickenpox": {
        "core": ["skin_rash", "itching"],
        "optional": ["fever", "fatigue", "headache", "loss_of_appetite"],
        "specialist": "Dermatologist",
        "department": "Dermatology",
        "severity": "moderate",
        "emergency": False,
        "advice": "Avoid scratching and keep skin clean. Isolate from others - it is contagious.",
    },
}

# Symptom-order independent list of every condition name the model knows.
CONDITION_NAMES = list(CONDITIONS.keys())

# --------------------------------------------------------------------------- #
# Helper accessors
# --------------------------------------------------------------------------- #
def symptom_aliases():
    """Map alias -> symptom key (lower-cased aliases)."""
    mapping = {}
    for key, meta in SYMPTOMS.items():
        for alias in meta["aliases"]:
            mapping[alias.strip().lower()] = key
    return mapping


def condition_for_symptom(key):
    """Conditions whose core/optional set includes this symptom key."""
    return [name for name, meta in CONDITIONS.items() if key in meta["core"] or key in meta["optional"]]


def related_symptoms(symptoms):
    """Rank related-but-unmentioned symptoms from conditions that match.

    Returns an ordered list of symptom keys the bot may probe next.
    """
    candidates = {}
    for sym in symptoms:
        for name in condition_for_symptom(sym):
            for candidate in CONDITIONS[name]["core"] + CONDITIONS[name]["optional"]:
                if candidate == sym:
                    continue
                candidates[candidate] = candidates.get(candidate, 0) + 1
    return [
        key for key, _ in sorted(
            candidates.items(), key=lambda pair: pair[1], reverse=True
        )
    ]


def specialist_for_condition(condition):
    return CONDITIONS.get(condition, {}).get("specialist", "General Physician")
