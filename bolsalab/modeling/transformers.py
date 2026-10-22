"""Paso de scikit-learn que cambia las variables antes del modelo.

Lo usa experiments.py para probar variantes de las 17 variables sin tocar
features.py. Va dentro del Pipeline, así que se aplica igual al entrenar y al
medir, y nunca mira la variable objetivo.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


class FeatureEngineer(BaseEstimator, TransformerMixin):
    """Quita variables, les saca logaritmo o multiplica pares de variables.

    drop: columnas que se quitan.
    log: columnas que se cambian por log(1 + valor).
    interactions: pares (a, b) que agregan la columna "a_x_b" = a * b.
    """

    def __init__(self, drop=(), log=(), interactions=()):
        self.drop = drop
        self.log = log
        self.interactions = interactions

    def fit(self, X: pd.DataFrame, y=None):
        missing = {*self.drop, *self.log, *(c for pair in self.interactions for c in pair)}
        missing -= set(X.columns)
        if missing:
            raise ValueError(f"Columnas que no existen en la tabla: {sorted(missing)}")
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        X = X.copy()
        for a, b in self.interactions:
            X[f"{a}_x_{b}"] = X[a] * X[b]
        for column in self.log:
            X[column] = np.log1p(X[column])
        return X.drop(columns=list(self.drop))
