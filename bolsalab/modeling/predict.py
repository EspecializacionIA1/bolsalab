"""Carga del modelo publicado y predicción para una persona.

La usan la app de Streamlit y el backend. Recibe las respuestas del
cuestionario y devuelve:

- la categoría: más, igual o menos propensa a vender que los inversionistas
  del estudio (protocolo, sección 8);
- las respuestas que más pesaron en el resultado, calculadas con SHAP;
- las preguntas de conocimiento que falló, para saber qué enseñarle;
- avisos cuando la persona queda fuera de lo que vio el modelo.

Nunca rehace el preprocesamiento: usa el Pipeline guardado en el .joblib.

Ejemplo:
    model = CrashReactionModel()
    model.predict({"age": 27, "male": False, "university": True, ...})
"""

import json
from pathlib import Path

import joblib
import pandas as pd
import shap

from bolsalab.config import MODELS_DIR

ARTIFACT = MODELS_DIR / "crash_reaction_v1.joblib"

# Respuesta correcta de cada pregunta de conocimiento (Bawalle et al., 2025, sección 2.3).
CORRECT = {"interest": "more", "inflation": "less", "diversification": "false"}
CHOICES = {
    "interest": {"more", "exactly", "less", "dont_know"},
    "inflation": {"more", "same", "less", "dont_know"},
    "diversification": {"true", "false", "dont_know"},
}
YES_NO = ["male", "university", "married", "has_children", "urban", "employed"]
LEVELS = {1: "bajo", 2: "medio bajo", 3: "medio", 4: "medio alto", 5: "alto"}
QUESTIONS = YES_NO + list(CHOICES) + ["age", "income_level", "assets_level",
                                      "knowledge_confidence"]

CATEGORIES = ("less_likely", "similar", "more_likely")
# Lo que la persona puede trabajar aprendiendo; el resto describe su situación.
ACTIONABLE = {"knows_interest", "knows_inflation", "knows_diversification",
              "knowledge_confidence", "overconfidence"}


def overconfident(confidence: int, correct: int) -> bool:
    """Regla del archivo japonés: marcó 5, o marcó 4 y acertó 2 o menos (protocolo, sección 3)."""
    return confidence == 5 or (confidence == 4 and correct <= 2)


def check_answers(answers: dict) -> None:
    """Detiene la predicción si falta una respuesta o trae un valor que no existe."""
    missing = [q for q in QUESTIONS if q not in answers]
    if missing:
        raise ValueError(f"Faltan respuestas: {missing}")
    for q, options in CHOICES.items():
        if answers[q] not in options:
            raise ValueError(f"{q} debe ser una de {sorted(options)}")
    for q in ["income_level", "assets_level", "knowledge_confidence"]:
        if answers[q] not in range(1, 6):
            raise ValueError(f"{q} debe ir de 1 a 5")


def build_features(answers: dict, reference: dict) -> pd.DataFrame:
    """Pasa las respuestas a las 17 variables del modelo, en su orden.

    `reference` es la metadata del modelo: trae los tramos japoneses de cada
    nivel de ingreso y activos y el valor de las preguntas que no se hacen.
    """
    check_answers(answers)
    knows = {q: int(answers[q] == CORRECT[q]) for q in CORRECT}
    confidence = int(answers["knowledge_confidence"])
    row = {
        "knows_interest": knows["interest"],
        "knows_inflation": knows["inflation"],
        "knows_diversification": knows["diversification"],
        "knowledge_confidence": confidence,
        "overconfidence": int(overconfident(confidence, sum(knows.values()))),
        "age": answers["age"],
        "age_squared": answers["age"] ** 2,
        **{q: int(bool(answers[q])) for q in YES_NO},
        "income_bracket": reference["income_level_to_bracket"][str(answers["income_level"])],
        "assets_bracket": reference["assets_level_to_bracket"][str(answers["assets_level"])],
        **reference["not_asked"],
    }
    return pd.DataFrame([row])[reference["features"]]


def factor_label(feature: str, answers: dict) -> str:
    """Texto corto de la respuesta detrás de cada factor."""
    yes = {
        "male": ("Eres hombre", "Eres mujer"),
        "university": ("Tienes título universitario", "No tienes título universitario"),
        "married": ("Estás casado(a)", "No estás casado(a)"),
        "has_children": ("Tienes hijos", "No tienes hijos"),
        "urban": ("Vives en una ciudad grande", "No vives en una ciudad grande"),
        "employed": ("Tienes empleo", "No tienes empleo"),
    }
    knowledge = {
        "knows_interest": ("interest", "interés compuesto"),
        "knows_inflation": ("inflation", "inflación"),
        "knows_diversification": ("diversification", "diversificación"),
    }
    if feature in yes:
        return yes[feature][0 if answers[feature] else 1]
    if feature in knowledge:
        question, topic = knowledge[feature]
        verb = "Acertaste" if answers[question] == CORRECT[question] else "No acertaste"
        return f"{verb} la pregunta de {topic}"
    if feature == "age":
        return f"Tu edad: {answers['age']} años"
    if feature == "knowledge_confidence":
        return f"Tu confianza en lo que sabes de finanzas: {answers['knowledge_confidence']} de 5"
    if feature == "overconfidence":
        correct = sum(answers[q] == CORRECT[q] for q in CORRECT)
        if overconfident(answers["knowledge_confidence"], correct):
            return "Te sientes más seguro(a) de lo que mostraron tus respuestas"
        return "Tu confianza va de acuerdo con tus respuestas"
    if feature == "income_bracket":
        return f"Ingreso de tu hogar: nivel {LEVELS[answers['income_level']]}"
    if feature == "assets_bracket":
        return f"Tus ahorros e inversiones: nivel {LEVELS[answers['assets_level']]}"
    raise KeyError(feature)


class CrashReactionModel:
    def __init__(self, artifact_path: str | Path = ARTIFACT):
        artifact_path = Path(artifact_path)
        self.pipeline = joblib.load(artifact_path)
        self.metadata = json.loads(artifact_path.with_suffix(".json").read_text(encoding="utf-8"))
        # Explicación exacta para árboles, en la escala interna del modelo (log-odds).
        self.explainer = shap.TreeExplainer(self.pipeline[-1])

    def explain(self, X: pd.DataFrame) -> pd.Series:
        """Aporte SHAP de cada variable para una persona. Edad y edad² van juntas."""
        # XGBoost no lleva preprocesamiento; otro ganador podría traer escalado antes.
        ready = self.pipeline[:-1].transform(X) if len(self.pipeline) > 1 else X
        values = pd.Series(self.explainer(ready).values[0], index=X.columns)
        values["age"] += values.pop("age_squared")
        return values.drop(list(self.metadata["not_asked"]))

    def category(self, probability: float) -> str:
        low, high = self.metadata["cutoffs"]
        return CATEGORIES[(probability >= low) + (probability >= high)]

    def predict(self, answers: dict, top: int = 4) -> dict:
        """Devuelve la categoría, los factores que más pesaron y los avisos."""
        X = build_features(answers, self.metadata)
        probability = float(self.pipeline.predict_proba(X)[0, 1])
        contributions = self.explain(X)
        strongest = contributions.abs().sort_values(ascending=False).index[:top]
        low_age, high_age = self.metadata["age_range"]
        return {
            "model_version": ARTIFACT.stem,
            "probability": probability,
            "base_rate": self.metadata["base_rate"],
            "category": self.category(probability),
            "top_factors": [
                {"feature": f, "label": factor_label(f, answers),
                 "direction": "increases" if contributions[f] > 0 else "decreases",
                 "impact": float(abs(contributions[f])),
                 "actionable": f in ACTIONABLE}
                for f in strongest
            ],
            "failed_questions": [q for q in CORRECT if answers[q] != CORRECT[q]],
            "overconfident": bool(X["overconfidence"].iloc[0]),
            "not_asked": list(self.metadata["not_asked"]),
            "warnings": [] if low_age <= answers["age"] <= high_age
            else ["age_outside_training_range"],
        }
