"""Train a RandomForest classifier on the synthetic symptom-disease dataset.

Loads data/symptom_disease.csv, splits into stratified train/test (80/20),
trains a RandomForestClassifier, prints test accuracy and a classification
report, then saves the model and the ordered symptom-column list to
models/ (the Streamlit app needs that exact column order).
"""

from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

RANDOM_STATE = 42
MODEL_PATH = Path(__file__).resolve().parent / "models" / "classifier.joblib"
SYMPTOM_LIST_PATH = Path(__file__).resolve().parent / "models" / "symptom_list.joblib"
DATA_PATH = Path(__file__).resolve().parent / "data" / "symptom_disease.csv"


def main():
    df = pd.read_csv(DATA_PATH)

    symptom_columns = [col for col in df.columns if col != "condition"]
    X = df[symptom_columns]
    y = df["condition"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )

    model = RandomForestClassifier(n_estimators=200, random_state=RANDOM_STATE)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print(f"Train size: {len(X_train)} | Test size: {len(X_test)}")
    print(f"Test accuracy: {accuracy:.4f}")
    print()
    print("Classification report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(symptom_columns, SYMPTOM_LIST_PATH)

    print(f"\nSaved model to: {MODEL_PATH}")
    print(f"Saved symptom list ({len(symptom_columns)} features) to: {SYMPTOM_LIST_PATH}")


if __name__ == "__main__":
    main()
