"""Experimentos con variables e hiperparámetros (exploración antes de train.py).

train.py hace la comparación oficial con las rejillas del protocolo. Este
módulo sirve para probar, uno tras otro, variantes de variables y rejillas más
amplias para un grupo de modelos, con exactamente las mismas reglas: la misma
partición, la validación anidada 5 x 3 y las mismas métricas (evaluate_model).

Nunca toca la prueba final (X_test). Cada experimento se guarda en
EXPERIMENTS_FILE en cuanto termina; si el proceso se corta, al volver a
ejecutarlo salta los que ya están hechos.

Uso: uv run python -m bolsalab.modeling.experiments [--model xgboost] [--rerun]
"""

import argparse
import json
from datetime import datetime

import pandas as pd
from sklearn.base import clone
from sklearn.pipeline import Pipeline

from bolsalab.config import MODELS_DIR
from bolsalab.modeling.train import MODELS, TRAINING_FILE, evaluate_model, split_data
from bolsalab.modeling.transformers import FeatureEngineer

EXPERIMENTS_FILE = MODELS_DIR / "experiments.csv"

# Modelos que se exploran (deben existir en MODELS de train.py).
MY_MODELS = ["xgboost", "lightgbm", "catboost"]

# Variantes de variables. "base" son las 17 variables de features.py sin cambios.
# Los nombres de columna son ejemplos: cámbialos por los reales.
FEATURE_SETS = {
    "base": {},
    "sin_edad_cuadrado": {"drop": ["edad_cuadrado"]},
    "log_ingreso": {"log": ["ingreso"]},
    "edad_x_ingreso": {"interactions": [("edad", "ingreso")]},
}

# Rejillas más amplias que las del protocolo. Cada modelo se prueba con la del
# protocolo (la de MODELS) y, si aparece aquí, también con la ampliada.
EXTRA_GRIDS = {
    "xgboost": {
        "model__learning_rate": [0.01, 0.03, 0.1],
        "model__max_depth": [3, 5, 7],
        "model__subsample": [0.8, 1.0],
        "model__min_child_weight": [1, 10],
    },
    "lightgbm": {
        "model__learning_rate": [0.01, 0.03, 0.1],
        "model__max_depth": [3, 5, 7],
        "model__num_leaves": [15, 31],
        "model__min_child_samples": [20, 100],
    },
    "catboost": {
        "model__learning_rate": [0.01, 0.03, 0.1],
        "model__depth": [4, 6, 8],
        "model__l2_leaf_reg": [1, 3, 10],
    },
}


def build_experiments():
    """Devuelve la lista de experimentos: (nombre, modelo, variante, rejilla).

    Combina cada modelo de MY_MODELS con cada variante de FEATURE_SETS y cada
    rejilla (protocolo y, si existe, ampliada).
    """
    experiments = []
    for model in MY_MODELS:
        grids = {"protocolo": MODELS[model][1]}
        if model in EXTRA_GRIDS:
            grids["ampliada"] = EXTRA_GRIDS[model]
        for features in FEATURE_SETS:
            for grid_name, grid in grids.items():
                experiments.append((f"{model}|{features}|{grid_name}", model, features, grid))
    return experiments


def make_pipeline(model: str, features: str) -> Pipeline:
    """Pipeline de MODELS con el paso "features" delante."""
    pipeline = clone(MODELS[model][0])
    return Pipeline([("features", FeatureEngineer(**FEATURE_SETS[features])), *pipeline.steps])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=MY_MODELS, help="solo los experimentos de este modelo")
    parser.add_argument("--rerun", action="store_true", help="repite los ya guardados")
    args = parser.parse_args()

    table = pd.read_parquet(TRAINING_FILE)
    X_train, _, y_train, _ = split_data(table)  # la prueba final no se usa aquí

    done = set()
    if EXPERIMENTS_FILE.exists() and not args.rerun:
        done = set(pd.read_csv(EXPERIMENTS_FILE)["experiment"])

    for name, model, features, grid in build_experiments():
        if (args.model and model != args.model) or name in done:
            continue
        print(f"  {name} ...", flush=True)
        row = {
            "experiment": name, "model": model, "features": features,
            "grid": json.dumps(grid, default=str),
            **evaluate_model(make_pipeline(model, features), grid, X_train, y_train),
            "run_at": datetime.now().isoformat(timespec="seconds"),
        }
        print(f"    AUROC {row['auroc']:.3f} ± {row['auroc_sd']:.3f}")
        MODELS_DIR.mkdir(exist_ok=True)
        pd.DataFrame([row]).to_csv(
            EXPERIMENTS_FILE, mode="a", header=not EXPERIMENTS_FILE.exists(), index=False)

    results = pd.read_csv(EXPERIMENTS_FILE).sort_values("auroc", ascending=False)
    cols = ["experiment", "auroc", "auroc_sd", "auprc", "brier", "calibration_slope"]
    print(results[cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()