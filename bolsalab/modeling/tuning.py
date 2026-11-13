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

import pandas as pd
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from bolsalab.config import RANDOM_STATE, REPORTS_DIR
from bolsalab.modeling.early_stopping import EarlyStoppingBooster
from bolsalab.modeling.train import TRAINING_FILE, evaluate_model, split_data

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


# Pruebas que busca Optuna: nombre -> número de intentos por partición externa.
SEARCHED_WITH_OPTUNA = {"xgboost|optuna": OPTUNA_TRIALS}


def trees_used(pipeline: Pipeline) -> int:
    """Cuántos árboles usó el modelo de una partición después de la parada temprana."""
    model = pipeline.named_steps["model"]
    if isinstance(model, EarlyStoppingBooster):
        return int(model.n_trees_)
    # CatBoost cuenta los árboles desde 0: si el mejor es el número 99, usó 100.
    return int(model.get_best_iteration()) + 1


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
    8: {
        "xgboost|optuna": (
            xgboost_with_optuna,
            "La rejilla solo prueba unos pocos valores; Optuna busca en rangos completos"),
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
        row = {
            "step": step, "experiment": name, "reason": reason,
            "grid": json.dumps(grid, default=str),
            **evaluate_model(pipeline, grid, X_train, y_train,
                             overfit_gap=True, fold_detail=trees_used,
                             n_trials=SEARCHED_WITH_OPTUNA.get(name)),
            "run_at": datetime.now().isoformat(timespec="seconds"),
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
