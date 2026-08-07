"""Reusable wrapper around the existing RandomForest symptom checker.

The classifier and the ordered symptom-column list are loaded once from
models/ (joblib) and cached at the process level, exactly the artifacts the
original project produced with train_model.py.
"""
import logging
from pathlib import Path

import joblib
import pandas as pd

logger = logging.getLogger(__name__)

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "classifier.joblib"
SYMPTOM_LIST_PATH = (
    Path(__file__).resolve().parent.parent / "models" / "symptom_list.joblib"
)


class DiseasePredictor:
    """Loads the RandomForest model once and exposes a symptom->top5 API."""

    def __init__(self, model_path=MODEL_PATH, symptom_list_path=SYMPTOM_LIST_PATH):
        self.model = joblib.load(model_path)
        self.symptom_list = joblib.load(symptom_list_path)
        self._friendly = {
            s: s.replace("_", " ").title() for s in self.symptom_list
        }
        logger.info("Loaded %s (%d features)", model_path, len(self.symptom_list))

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def predict(self, symptoms):
        """Return the top-5 diseases with confidence % for a symptom list.

        Args:
            symptoms: iterable of symptom keys (e.g. ["fever", "cough"]).
        Returns:
            list of {"disease", "confidence"} sorted desc by confidence.
        """
        present = set(symptoms)
        row = pd.DataFrame(
            [[1.0 if s in present else 0.0 for s in self.symptom_list]],
            columns=self.symptom_list,
        )
        probabilities = self.model.predict_proba(row)[0]
        classes = self.model.classes_

        ranked = sorted(
            zip(classes, probabilities), key=lambda pair: pair[1], reverse=True
        )
        return [
            {"disease": name, "confidence": round(float(prob) * 100.0, 1)}
            for name, prob in ranked[:5]
        ]

    def symptom_label(self, key):
        """Human-readable label for a symptom key."""
        return self._friendly.get(key, key.replace("_", " ").title())

    def all_symptoms(self):
        """Return every supported symptom key (53 features)."""
        return list(self.symptom_list)

    def supported_symptoms(self):
        """Return [{"key", "label"}] for the symptom-selection UI."""
        return [
            {"key": s, "label": self._friendly[s]} for s in self.symptom_list
        ]


# Process-wide singleton so the 6.9 MB model is deserialized only once.
_predictor = None


def get_predictor():
    global _predictor
    if _predictor is None:
        _predictor = DiseasePredictor()
    return _predictor
