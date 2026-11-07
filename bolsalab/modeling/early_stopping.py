"""Parada temprana para XGBoost y LightGBM dentro de la validación anidada.

Con parada temprana el modelo agrega árboles mientras mejore en un pedazo de
validación y se detiene cuando deja de mejorar. Así el número de árboles lo
decide el modelo y no queda fijo en 300.

XGBoost y LightGBM necesitan que se les pase ese pedazo al entrenar, y
GridSearchCV no sabe pasarlo. Este envoltorio lo aparta dentro de cada
entrenamiento: el 10 % de las personas que recibe, con la misma proporción de
ventas. Como solo usa los datos que ya le tocaron a esa partición, nunca ve a
las personas con las que se mide y no hay fuga. CatBoost no lo necesita: hace
lo mismo con su parámetro eval_fraction.
"""

import lightgbm
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

from bolsalab.config import RANDOM_STATE


class EarlyStoppingBooster(ClassifierMixin, BaseEstimator):
    """Entrena un XGBClassifier o LGBMClassifier con parada temprana.

    estimator: el modelo, con n_estimators como tope de árboles.
    validation_fraction: parte de los datos recibidos que se aparta para decidir cuándo parar.
    patience: cuántos árboles seguidos sin mejorar se esperan antes de parar.

    Después de fit, n_trees_ dice cuántos árboles usó.
    """

    def __init__(self, estimator, validation_fraction=0.1, patience=50,
                 random_state=RANDOM_STATE):
        self.estimator = estimator
        self.validation_fraction = validation_fraction
        self.patience = patience
        self.random_state = random_state

    def fit(self, X, y):
        X_fit, X_val, y_fit, y_val = train_test_split(
            X, y, test_size=self.validation_fraction, stratify=y,
            random_state=self.random_state)
        model = clone(self.estimator)
        if isinstance(model, XGBClassifier):
            model.set_params(early_stopping_rounds=self.patience)
            model.fit(X_fit, y_fit, eval_set=[(X_val, y_val)], verbose=False)
            self.n_trees_ = model.best_iteration + 1
        elif isinstance(model, lightgbm.LGBMClassifier):
            model.fit(X_fit, y_fit, eval_X=X_val, eval_y=y_val,
                      callbacks=[lightgbm.early_stopping(self.patience, verbose=False)])
            self.n_trees_ = model.best_iteration_
        else:
            raise TypeError("Solo se admite XGBClassifier o LGBMClassifier")
        self.estimator_ = model
        self.classes_ = model.classes_
        return self

    def predict_proba(self, X):
        # Los dos modelos usan solo los árboles hasta el mejor punto.
        return self.estimator_.predict_proba(X)

    def predict(self, X):
        return self.estimator_.predict(X)
