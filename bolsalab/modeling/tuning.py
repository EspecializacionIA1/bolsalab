"""Ajuste por familias de modelos (docs/plan-ajuste-por-familias.md).

Cada prueba tiene una razón que sale de cómo aprende el modelo, y el resultado
de un paso decide el siguiente. Usa las mismas reglas que train.py y
experiments.py: la misma partición, la validación anidada 5 x 3
(evaluate_model) y las mismas métricas. Además mide la brecha de sobreajuste.
Nunca toca la prueba final (X_test).

Cada prueba se guarda en TUNING_FILE en cuanto termina; si el proceso se corta,
al volver a ejecutarlo salta las que ya están hechas.

Uso: uv run python -m bolsalab.modeling.tuning --step 1 [--rerun]
"""

import argparse
import json
from datetime import datetime
from functools import partial

import numpy as np
import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.base import BaseEstimator, ClassifierMixin, clone
from sklearn.ensemble import VotingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from bolsalab.config import RANDOM_STATE, REPORTS_DIR
from bolsalab.dataset import INVESTORS_FILE
from bolsalab.modeling.early_stopping import EarlyStoppingBooster
from bolsalab.modeling.train import TRAINING_FILE, evaluate_model, split_data
from bolsalab.modeling.transformers import FeatureEngineer

TUNING_FILE = REPORTS_DIR / "tuning.csv"

# Paso 1: parada temprana. Tope de 2.000 árboles, se para tras 50 sin mejorar y
# se aparta el 10 % para decidirlo (decisión nuestra, registrada en el plan).
# Las velocidades y profundidades son las del protocolo, para que la única 
# diferencia con la comparación oficial sea el número de árboles.
MAX_TREES = 2000
PATIENCE = 50
VALIDATION_FRACTION = 0.1

# Cómo leer los nombres de las rejillas: el doble guion bajo significa "entra a".
# "model__estimator__learning_rate" es: en el paso "model" del Pipeline, entra
# al modelo envuelto ("estimator") y cambia su learning_rate.


def xgboost_with_early_stopping():
    """XGBoost que decide cuántos árboles usar, con la rejilla del protocolo."""
    model = EarlyStoppingBooster(
        XGBClassifier(n_estimators=MAX_TREES, random_state=RANDOM_STATE),
        validation_fraction=VALIDATION_FRACTION, patience=PATIENCE)
    grid = {"model__estimator__learning_rate": [0.03, 0.1],
            "model__estimator__max_depth": [3, 5]}
    return Pipeline([("model", model)]), grid


def lightgbm_with_early_stopping():
    """LightGBM que decide cuántos árboles usar, con la rejilla del protocolo."""
    model = EarlyStoppingBooster(
        LGBMClassifier(n_estimators=MAX_TREES, random_state=RANDOM_STATE, verbose=-1),
        validation_fraction=VALIDATION_FRACTION, patience=PATIENCE)
    grid = {"model__estimator__learning_rate": [0.03, 0.1],
            "model__estimator__max_depth": [3, 5]}
    return Pipeline([("model", model)]), grid


def catboost_with_early_stopping():
    """CatBoost que decide cuántos árboles usar; aparta su validación solo."""
    model = CatBoostClassifier(
        iterations=MAX_TREES, early_stopping_rounds=PATIENCE,
        eval_fraction=VALIDATION_FRACTION, random_seed=RANDOM_STATE,
        verbose=0, allow_writing_files=False)
    grid = {"model__learning_rate": [0.03, 0.1], "model__depth": [4, 6]}
    return Pipeline([("model", model)]), grid


# Paso 2: poda de cada árbol, sobre la parada temprana del paso 1. La
# profundidad queda en 3 porque fue la que eligieron las 15 particiones de
# XGBoost y LightGBM en el paso 1; la velocidad sigue con las dos opciones
# porque las particiones se repartieron entre 0,03 y 0,1.
#   gamma / min_split_gain: un corte solo se hace si mejora al menos este valor.
#   reg_lambda: castiga las hojas con riesgos extremos y las acerca al promedio.
# Cada rejilla empieza en el valor por defecto de su librería (gamma 0 y
# reg_lambda 1 en XGBoost; min_split_gain 0 y reg_lambda 0 en LightGBM).
SPLIT_GAIN_VALUES = [0, 0.5, 1, 2]


def xgboost_with_pruning():
    """El XGBoost del paso 1 con la poda propia de XGBoost: gamma y reg_lambda."""
    pipeline, _ = xgboost_with_early_stopping()
    grid = {"model__estimator__learning_rate": [0.03, 0.1],
            "model__estimator__max_depth": [3],
            "model__estimator__gamma": SPLIT_GAIN_VALUES,
            "model__estimator__reg_lambda": [1, 5, 10]}
    return pipeline, grid


def lightgbm_with_pruning():
    """El LightGBM del paso 1 con su poda equivalente: min_split_gain y reg_lambda."""
    pipeline, _ = lightgbm_with_early_stopping()
    grid = {"model__estimator__learning_rate": [0.03, 0.1],
            "model__estimator__max_depth": [3],
            "model__estimator__min_split_gain": SPLIT_GAIN_VALUES,
            "model__estimator__reg_lambda": [0, 5, 10]}
    return pipeline, grid


# Paso 5: variables. El modelo y la rejilla son los del paso 2 (XGBoost con poda);
# lo único que cambia entre pruebas son las columnas. Así, si el AUROC se mueve,
# es por la variable y no por el ajuste. Se compara con "xgboost|poda" del paso 2.
def xgboost_with_variables(**changes):
    """El XGBoost del paso 2 con un cambio en las variables (ver FeatureEngineer)."""
    pipeline, grid = xgboost_with_pruning()
    pipeline.steps.insert(0, ("variables", FeatureEngineer(**changes)))
    if changes.get("categorical"):
        # XGBoost solo trata una columna como grupos si se le pide.
        pipeline.set_params(model__estimator__enable_categorical=True)
    return pipeline, grid


# Paso 8: los mismos cuatro hiperparámetros del paso 2, pero buscados con Optuna.
# La rejilla solo prueba los valores de una lista. Optuna recibe un rango, prueba
# una combinación, mira el AUROC y con eso decide cuál probar después.
# Los rangos cubren la rejilla del paso 2 y se abren más allá de sus bordes,
# porque varias particiones eligieron el borde (reg_lambda 10).
# Cada rango es (tipo, mínimo, máximo). El tipo "log" reparte los intentos por
# escala: tantos entre 0,01 y 0,1 como entre 0,1 y 1.
OPTUNA_TRIALS = 50


def xgboost_with_optuna():
    """El XGBoost del paso 1 con rangos para Optuna en vez de una rejilla."""
    pipeline, _ = xgboost_with_early_stopping()
    ranges = {"model__estimator__learning_rate": ("log", 0.01, 0.3),
              "model__estimator__max_depth": ("int", 2, 6),
              "model__estimator__gamma": ("float", 0, 5),
              "model__estimator__reg_lambda": ("log", 0.1, 20)}
    return pipeline, ranges


# Paso 9: dos ideas de la literatura (protocolo, sección 7).
#
# Aleatoriedad, de la guía de XGBoost ("Notes on Parameter Tuning"):
#   subsample: cada árbol aprende con una parte de las personas.
#   colsample_bytree: cada árbol mira una parte de las preguntas.
#   min_child_weight: mínimo de "peso" por hoja. Cada persona pesa como mucho
#   0,25, así que 100 pide al menos 400 personas por hoja.
# Mismos rangos y 50 intentos del paso 8: la única diferencia son estas tres.
def xgboost_with_randomness():
    """El XGBoost del paso 8 con tres controles más contra el sobreajuste."""
    pipeline, ranges = xgboost_with_optuna()
    ranges = {**ranges,
              "model__estimator__subsample": ("float", 0.5, 1),
              "model__estimator__colsample_bytree": ("float", 0.5, 1),
              "model__estimator__min_child_weight": ("log", 1, 100)}
    return pipeline, ranges


# Promedio, de TabArena (2025) y Shwartz-Ziv y Armon (2021): se promedian las
# probabilidades de tres modelos distintos, con el mismo peso y sin ajustar pesos.
# Cada uno va con lo que eligió la mayoría de las 5 particiones en su paso:
#   XGBoost del paso 2: velocidad 0,03 (3 de 5), gamma 0,5 (la mediana), reg_lambda 10 (5 de 5).
#   CatBoost del paso 1: velocidad 0,03 (5 de 5), profundidad 4 (4 de 5).
#   Regresión logística: C = 1; con C de 0,01 a 10 el AUROC da 0,6456 en todos.
def average_of_models():
    """Promedio simple de XGBoost, CatBoost y regresión logística."""
    xgboost = EarlyStoppingBooster(
        XGBClassifier(n_estimators=MAX_TREES, learning_rate=0.03, max_depth=3, gamma=0.5,
                      reg_lambda=10, random_state=RANDOM_STATE),
        validation_fraction=VALIDATION_FRACTION, patience=PATIENCE)
    catboost = CatBoostClassifier(
        iterations=MAX_TREES, learning_rate=0.03, depth=4, early_stopping_rounds=PATIENCE,
        eval_fraction=VALIDATION_FRACTION, random_seed=RANDOM_STATE,
        verbose=0, allow_writing_files=False)
    logistic = Pipeline([("scale", StandardScaler()),
                         ("model", LogisticRegression(max_iter=1000))])
    average = VotingClassifier(
        [("xgboost", xgboost), ("catboost", catboost), ("logistic", logistic)], voting="soft")
    # Sin rejilla: los tres modelos ya traen sus valores.
    return Pipeline([("model", average)]), {}


# Paso 10: etiqueta de tres clases (protocolo, sección 7). El modelo aprende
# tres respuestas en vez de dos: 0 = mantuvo, 1 = vendió parte, 2 = vendió todo.
# Para calificarlo se suma la probabilidad de las dos ventas y se mide contra
# `sold`, igual que las demás pruebas.
HELD, SOLD_PART, SOLD_ALL = 0, 1, 2


def load_sale_type(index: pd.Index) -> np.ndarray:
    """Tipo de venta de cada persona, en el orden de `index`.

    La tabla de entrenamiento tiene las mismas filas, en el mismo orden, que
    INVESTORS_FILE; por eso el índice de X_train sirve para buscarlas.
    """
    investors = pd.read_parquet(INVESTORS_FILE, columns=["Tot_Panic_Sell", "Part_Panic_Sell"])
    kind = np.where(investors["Tot_Panic_Sell"] == 1, SOLD_ALL,
                    np.where(investors["Part_Panic_Sell"] == 1, SOLD_PART, HELD))
    return kind[index]


class ThreeClassModel(ClassifierMixin, BaseEstimator):
    """Aprende las tres respuestas y devuelve la probabilidad de vender.

    fit recibe, además de `sold`, el tipo de venta de cada persona; lo usa solo
    para entrenar. predict_proba devuelve dos columnas, como cualquier modelo
    de `sold`: [P(mantuvo), P(vendió parte) + P(vendió todo)].
    """

    def __init__(self, estimator):
        self.estimator = estimator

    def fit(self, X, y, sale_type):
        # El tipo de venta tiene que decir lo mismo que `sold`: si no, está desordenado.
        if not np.array_equal(np.asarray(sale_type) != HELD, np.asarray(y) == 1):
            raise ValueError("El tipo de venta no coincide con `sold`")
        self.estimator_ = clone(self.estimator).fit(X, sale_type)
        self.classes_ = np.array([0, 1])
        return self

    def predict_proba(self, X):
        p = self.estimator_.predict_proba(X)
        # Suma las columnas de las ventas según las clases que vio el modelo, no por posición.
        sold = p[:, self.estimator_.classes_ != HELD].sum(axis=1)
        return np.column_stack([1 - sold, sold])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)


def xgboost_with_three_classes():
    """El XGBoost con poda del paso 2, con la misma rejilla, aprendiendo tres clases."""
    pipeline, grid = xgboost_with_pruning()
    model = ThreeClassModel(pipeline.named_steps["model"])
    # La rejilla entra un nivel más: model -> estimator (parada temprana) -> estimator (XGBoost).
    grid = {name.replace("model__", "model__estimator__", 1): values
            for name, values in grid.items()}
    return Pipeline([("model", model)]), grid


# Pruebas que busca Optuna: nombre -> número de intentos por partición externa.
SEARCHED_WITH_OPTUNA = {"xgboost|optuna": OPTUNA_TRIALS,
                        "xgboost|aleatoriedad": OPTUNA_TRIALS}

# Pruebas que reciben el tipo de venta al entrenar.
USES_SALE_TYPE = {"etiqueta|tres_clases"}


def count_trees(model) -> int | None:
    """Cuántos árboles usó un boosting después de la parada temprana; None si no tiene árboles."""
    if isinstance(model, ThreeClassModel):
        # Con tres clases, cada ronda de boosting hace un árbol por clase.
        return count_trees(model.estimator_) * len(model.estimator_.classes_)
    if isinstance(model, EarlyStoppingBooster):
        return int(model.n_trees_)
    if isinstance(model, CatBoostClassifier):
        # CatBoost cuenta los árboles desde 0: si el mejor es el número 99, usó 100.
        return int(model.get_best_iteration()) + 1
    return None


def trees_used(pipeline: Pipeline):
    """Árboles que usó el modelo de una partición; en el promedio, los de cada boosting."""
    model = pipeline.named_steps["model"]
    if isinstance(model, VotingClassifier):
        trees = {name: count_trees(member) for name, member in model.named_estimators_.items()}
        return {name: n for name, n in trees.items() if n is not None}
    return count_trees(model)


# Pruebas por paso: nombre -> (función que arma el pipeline y su rejilla, por qué).
STEPS = {
    1: {
        "xgboost|parada_temprana": (
            xgboost_with_early_stopping,
            "300 árboles fijos con velocidad 0,03 pueden quedarse cortos o sobrar"),
        "lightgbm|parada_temprana": (
            lightgbm_with_early_stopping,
            "Mismo motivo que XGBoost; también usaba 300 árboles fijos"),
        "catboost|parada_temprana": (
            catboost_with_early_stopping,
            "Mismo motivo; CatBoost aparta la validación con eval_fraction"),
    },
    2: {
        "xgboost|poda": (
            xgboost_with_pruning,
            "Siempre elige la profundidad mínima: hay mucho ruido y cada corte debe valer la pena"),
        "lightgbm|poda": (
            lightgbm_with_pruning,
            "Mismo motivo, con min_split_gain, que es el equivalente de gamma"),
    },
    5: {
        "variables|total_aciertos": (
            partial(xgboost_with_variables, add_correct_answers=True),
            "Tres preguntas miden lo mismo y a un árbol de 3 niveles le cuesta sumarlas"),
        "variables|confianza_sin_sustento": (
            partial(xgboost_with_variables, unjustified_confidence=True),
            "La columna actual marca también a quien confía y acertó todo; el artículo no"),
        "variables|hombre_pocos_aciertos": (
            partial(xgboost_with_variables, man_with_few_correct=True),
            "Exploratoria: fallar las preguntas pesa casi el doble en los hombres"),
        "variables|poco_colchon": (
            partial(xgboost_with_variables, low_financial_cushion=True),
            "Quien gana poco y tiene pocos ahorros no puede aguantar una pérdida"),
        "variables|tramos_como_grupos": (
            partial(xgboost_with_variables, categorical=("income_bracket", "assets_bracket")),
            "El tramo 6 no es el doble del tramo 3: los tramos son grupos, no cantidades"),
        "variables|solo_app": (
            partial(xgboost_with_variables, drop=("risk_aversion", "short_term_view")),
            "La app no pregunta estas dos; queremos saber cuánto AUROC cuesta quitarlas"),
    },
    8: {
        "xgboost|optuna": (
            xgboost_with_optuna,
            "La rejilla solo prueba unos pocos valores; Optuna busca en rangos completos"),
    },
    9: {
        "xgboost|aleatoriedad": (
            xgboost_with_randomness,
            "La guía de XGBoost recomienda que cada árbol vea solo una parte de los datos"),
        "promedio|xgboost_catboost_logistica": (
            average_of_models,
            "En los benchmarks de datos en tabla, promediar modelos distintos rinde más que uno solo"),
    },
    10: {
        "etiqueta|tres_clases": (
            xgboost_with_three_classes,
            "`sold` junta a quien vendió todo y a quien vendió parte; verlos por separado podría ayudar"),
    },
}


def run_step(step: int, X_train: pd.DataFrame, y_train: pd.Series, rerun: bool = False) -> None:
    """Corre las pruebas de un paso y guarda cada una en TUNING_FILE apenas termina.

    Salta las que ya están guardadas, salvo con rerun=True. Lo usan main() y el
    notebook "Ajuste por familias".
    """
    done = set()
    if TUNING_FILE.exists() and not rerun:
        done = set(pd.read_csv(TUNING_FILE)["experiment"])

    for name, (build, reason) in STEPS[step].items():
        if name in done:
            continue
        print(f"  {name} ...", flush=True)
        pipeline, grid = build()
        fit_params = None
        if name in USES_SALE_TYPE:
            fit_params = {"model__sale_type": load_sale_type(X_train.index)}
        row = {
            "step": step, "experiment": name, "reason": reason,
            "grid": json.dumps(grid, default=str),
            **evaluate_model(pipeline, grid, X_train, y_train,
                             overfit_gap=True, fold_detail=trees_used,
                             n_trials=SEARCHED_WITH_OPTUNA.get(name),
                             fit_params=fit_params),
            "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        }
        print(f"    AUROC {row['auroc']:.4f} ± {row['auroc_sd']:.4f} · "
              f"brecha {row['overfit_gap']:.4f} · árboles {row['fold_detail']}")
        REPORTS_DIR.mkdir(exist_ok=True)
        pd.DataFrame([row]).to_csv(
            TUNING_FILE, mode="a", header=not TUNING_FILE.exists(), index=False)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--step", type=int, choices=sorted(STEPS), required=True)
    parser.add_argument("--rerun", action="store_true", help="repite las ya guardadas")
    args = parser.parse_args()

    table = pd.read_parquet(TRAINING_FILE)
    X_train, _, y_train, _ = split_data(table)  # la prueba final no se usa aquí
    run_step(args.step, X_train, y_train, rerun=args.rerun)

    results = pd.read_csv(TUNING_FILE).sort_values("auroc", ascending=False)
    cols = ["experiment", "auroc", "auroc_sd", "overfit_gap", "calibration_slope", "fold_detail"]
    print(results[cols].round(4).to_string(index=False))


if __name__ == "__main__":
    main()
