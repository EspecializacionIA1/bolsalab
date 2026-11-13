"""Paso de scikit-learn que cambia las variables antes del modelo.

Lo usan experiments.py y tuning.py para probar variantes de las 17 variables sin
tocar features.py. Va dentro del Pipeline, así que se aplica igual al entrenar
y al medir, y nunca mira la variable objetivo.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin

QUESTIONS = ["knows_interest", "knows_inflation", "knows_diversification"]

# Cortes de las variables nuevas (decisión nuestra, protocolo sección 7).
CONFIDENT_FROM = 4       # "confiado": confianza 4 o 5, de 1 a 5
FEW_CORRECT_UP_TO = 1    # "pocos aciertos": 0 o 1, de 3
LOW_BRACKET_UP_TO = 2    # "tramo bajo": los dos tramos más bajos


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Quita, transforma o agrega variables.

    drop: columnas que se quitan.
    log: columnas que se cambian por log(1 + valor).
    interactions: pares (a, b) que agregan la columna "a_x_b" = a * b.
    categorical: columnas que el modelo debe tratar como grupos y no como números.
    add_correct_answers: agrega "correct_answers", los aciertos de 0 a 3.
    unjustified_confidence: cambia "overconfidence" por "unjustified_confidence",
        la definición del artículo: menos aciertos que el promedio y confiado.
    man_with_few_correct: agrega la marca de hombre con 0 o 1 aciertos.
    low_financial_cushion: agrega la marca de ingreso bajo y activos bajos.
    """

    def __init__(self, drop=(), log=(), interactions=(), categorical=(),
                 add_correct_answers=False, unjustified_confidence=False,
                 man_with_few_correct=False, low_financial_cushion=False):
        self.drop = drop
        self.log = log
        self.interactions = interactions
        self.categorical = categorical
        self.add_correct_answers = add_correct_answers
        self.unjustified_confidence = unjustified_confidence
        self.man_with_few_correct = man_with_few_correct
        self.low_financial_cushion = low_financial_cushion

    def fit(self, X: pd.DataFrame, y=None):
        missing = {*self.drop, *self.log, *self.categorical,
                   *(c for pair in self.interactions for c in pair)}
        missing -= set(X.columns)
        if missing:
            raise ValueError(f"Columnas que no existen en la tabla: {sorted(missing)}")
        # Lo que se aprende aquí sale solo de las personas de entrenamiento.
        if self.unjustified_confidence:
            self.mean_correct_ = X[QUESTIONS].sum(axis=1).mean()
        self.categories_ = {column: sorted(X[column].unique()) for column in self.categorical}
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for a, b in self.interactions:
            X[f"{a}_x_{b}"] = X[a] * X[b]
        for column in self.log:
            X[column] = np.log1p(X[column])

        if self.add_correct_answers:
            X["correct_answers"] = X[QUESTIONS].sum(axis=1)
        if self.unjustified_confidence:
            few_correct = X[QUESTIONS].sum(axis=1) < self.mean_correct_
            confident = X["knowledge_confidence"] >= CONFIDENT_FROM
            X["unjustified_confidence"] = (few_correct & confident).astype(int)
            X = X.drop(columns="overconfidence")
        if self.man_with_few_correct:
            few_correct = X[QUESTIONS].sum(axis=1) <= FEW_CORRECT_UP_TO
            X["man_with_few_correct"] = ((X["male"] == 1) & few_correct).astype(int)
        if self.low_financial_cushion:
            low_income = X["income_bracket"] <= LOW_BRACKET_UP_TO
            low_assets = X["assets_bracket"] <= LOW_BRACKET_UP_TO
            X["low_financial_cushion"] = (low_income & low_assets).astype(int)

        for column in self.categorical:
            X[column] = pd.Categorical(X[column], categories=self.categories_[column])
        return X.drop(columns=list(self.drop))
