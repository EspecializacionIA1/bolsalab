"""Búsqueda de hiperparámetros con Optuna dentro de la validación anidada.

GridSearchCV prueba todas las combinaciones de una lista fija. Optuna recibe
rangos: prueba una combinación, mira el AUROC que dio y con eso decide cuál
probar después, así gasta más intentos cerca de las que van mejor.

Esta clase hace el mismo trabajo que GridSearchCV y se usa en su lugar: mide
cada combinación con las particiones internas, se queda con la mejor y entrena
el modelo final con ella. Como solo ve los datos que le pasa la partición
externa, nunca usa a las personas con las que se mide.
"""

import optuna
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.model_selection import cross_val_score

from bolsalab.config import RANDOM_STATE


def suggest(trial, name, kind, low, high):
    """Le pide a Optuna un valor para un hiperparámetro dentro de su rango.

    kind: "int" para enteros, "float" para decimales, y "log" para decimales
    repartidos por escala (tantos intentos entre 0,01 y 0,1 como entre 0,1 y 1).
    """
    if kind == "int":
        return trial.suggest_int(name, low, high)
    return trial.suggest_float(name, low, high, log=(kind == "log"))


class OptunaSearch(ClassifierMixin, BaseEstimator):
    """Elige los hiperparámetros de un pipeline con Optuna.

    pipeline: el modelo a ajustar.
    ranges: hiperparámetro -> (kind, mínimo, máximo).
    n_trials: cuántas combinaciones prueba.
    cv: las particiones internas con las que mide cada combinación.

    Después de fit, best_params_ tiene la combinación ganadora y
    best_estimator_ el modelo entrenado con ella.
    """

    def __init__(self, pipeline, ranges, n_trials, cv, random_state=RANDOM_STATE):
        self.pipeline = pipeline
        self.ranges = ranges
        self.n_trials = n_trials
        self.cv = cv
        self.random_state = random_state

    def fit(self, X, y):
        def auroc(trial):
            params = {name: suggest(trial, name, *range_)
                      for name, range_ in self.ranges.items()}
            model = clone(self.pipeline).set_params(**params)
            return cross_val_score(model, X, y, cv=self.cv, scoring="roc_auc").mean()

        optuna.logging.set_verbosity(optuna.logging.WARNING)
        sampler = optuna.samplers.TPESampler(seed=self.random_state)
        study = optuna.create_study(direction="maximize", sampler=sampler)
        study.optimize(auroc, n_trials=self.n_trials, show_progress_bar=True)

        self.best_params_ = study.best_params
        self.best_score_ = study.best_value
        self.best_estimator_ = clone(self.pipeline).set_params(**self.best_params_).fit(X, y)
        self.classes_ = self.best_estimator_.classes_
        return self

    def predict_proba(self, X):
        return self.best_estimator_.predict_proba(X)

    def predict(self, X):
        return self.best_estimator_.predict(X)
