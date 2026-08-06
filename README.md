# Symptom Checker Assistant 🩺

An end-to-end machine-learning capstone project that predicts **likely medical
conditions** from a set of selected symptoms.

> ⚠️ **This is an educational demo, not medical advice.** The model is trained
> on **synthetic** data and is not clinically validated. It cannot diagnose you.
> For real health concerns, consult a doctor; for anything urgent, call your
> local emergency services.

## What it does

1. `generate_data.py` invents ~800 synthetic patient cases (40 per condition)
   across **20 common, non-emergency conditions** (Common Cold, Flu, Migraine,
   Allergic Rhinitis, Gastroenteritis, Sinusitis, UTI, and more). Each case is
   a 0/1 row: core symptoms always on, optional symptoms ~50% of the time, plus
   a ~15% chance of one random unrelated symptom for noise.
2. `train_model.py` trains a `RandomForestClassifier` (200 trees) on those rows
   and saves the model plus the ordered symptom column list to `models/`.
3. `app.py` is a Streamlit UI where users pick symptoms and see the top 5
   conditions with probability bars — always framed with clear disclaimers.

## Project structure

```
medical-assistant/
├── data/                  # generated dataset (symptom_disease.csv)
├── models/                # classifier.joblib + symptom_list.joblib
├── generate_data.py       # creates synthetic data
├── train_model.py         # trains + saves the model
├── app.py                 # Streamlit UI
├── requirements.txt
└── README.md
```

## Run it locally

Requires Python 3.9+.

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate the synthetic dataset
python generate_data.py

# 3. Train the model (prints accuracy + classification report)
python train_model.py

# 4. Launch the app
streamlit run app.py
```

Then open the local URL Streamlit prints (usually http://localhost:8501).

## Deploy on Streamlit Community Cloud

1. Push this folder to a GitHub repository.
2. Go to https://share.streamlit.io (or the Streamlit Community Cloud), sign in,
   and click **"New app"**.
3. Pick your repo and branch, set **Main file path** to `app.py`, and click
   **Deploy**.
4. Streamlit auto-installs `requirements.txt`. Make sure `models/*.joblib` are
   committed so the app can load them (you can also download the dataset/model
   at startup and cache them with `st.cache_resource` if you prefer not to
   commit binary files).

## Swap in a real dataset

The pipeline expects one row per patient case, one **0/1 column per symptom**,
and a final `condition` column:

```
runny_nose, sneezing, sore_throat, ..., condition
1, 0, 1, ..., Common Cold
```

To use a real dataset such as Kaggle's *Disease Symptom Prediction* dataset:

1. Convert its symptom columns to the same 0/1 shape (the datasets are usually
   already in this "wide" one-hot format).
2. Save it as `data/symptom_disease.csv` (or point `train_model.py` at your
   file).
3. Re-run `python train_model.py` to retrain and save new model/symptom-list
   files.
4. The app picks up the new files automatically — its symptom labels fall back
   to a human-readable title case if an unknown column name appears.

## Presentation talking points

- **Scoping choices.** Why "common, non-emergency" conditions only (a safety and
  scope decision), why synthetic data (no privacy/ethics issues, full control of
  the label distribution), and why `RandomForest` over deep learning (small
  feature space, tabular data, interpretability, fast to train on a laptop).
- **Safety framing.** The product decision to always show a persistent disclaimer,
  gate the button on input, present **top-5 probabilities instead of a single
  "answer"**, and repeatedly call out "statistical match, not diagnosis."
- **The pipeline.** Data generation → train/test split → classification report →
  joblib serialization → cached model loading in Streamlit → one-hot input row.
- **Live demo.** Run `streamlit run app.py`, pick a few symptoms, and show the
  top-5 bars. Mention how the "noise" rows (one random unrelated symptom) keep
  the task non-trivial, then mention how to swap in real data and retrain.

## Disclaimer

This project is for education and portfolio demonstration only. It must not be
used to make medical decisions.
