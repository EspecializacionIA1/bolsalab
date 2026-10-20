"""Entrenamiento, comparación y exportación del modelo (etapa 3 del pipeline).

Es el paso donde el modelo aprende. Toma la tabla de entrenamiento de
features.py (54.704 personas, 17 variables y `sold`), entrena varios modelos,
los compara con las mismas reglas y guarda el ganador para que la API lo use.

Todas las reglas salen de docs/protocolo-evaluacion.md (secciones 4 a 7).

Uso: uv run python -m bolsalab.modeling.train
"""

import json
from datetime import date

import joblib
import numpy as np
import pandas as pd
import sklearn
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, make_scorer, roc_auc_score
from sklearn.model_selection import GridSearchCV, StratifiedKFold, cross_validate, train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from bolsalab.config import MODELS_DIR, PROCESSED_DATA_DIR, RANDOM_STATE

TRAINING_FILE = PROCESSED_DATA_DIR / "japan_training.parquet"
TARGET = "sold"

# Un modelo por línea, de más simple a más complejo:
#   nombre -> (Pipeline de scikit-learn, rangos de hiperparámetros)
# El Pipeline junta el preprocesamiento y el modelo, para que el escalado se
# aprenda solo con los datos de entrenamiento. Rangos: sección 7 del protocolo.
MODELS = {
    # Jenny
    "trivial": (
        Pipeline([("model", DummyClassifier(strategy="prior"))]),
        {},
    ),
    "logistic": (
        Pipeline([("scale", StandardScaler()),
                  ("model", LogisticRegression(max_iter=1000))]),
        {"model__C": [0.01, 0.1, 1, 10]},
    ),
    # Luis
    "random_forest": (
        Pipeline([("model", RandomForestClassifier(
            n_estimators=300, random_state=RANDOM_STATE, n_jobs=-1))]),
        {"model__max_depth": [4, 8, None], "model__min_samples_leaf": [20, 100]},
    ),
    # Dilan
    "xgboost": (
        Pipeline([("model", XGBClassifier(n_estimators=300, random_state=RANDOM_STATE))]),
        {"model__learning_rate": [0.03, 0.1], "model__max_depth": [3, 5]},
    ),
    "lightgbm": (
        Pipeline([("model", LGBMClassifier(
            n_estimators=300, random_state=RANDOM_STATE, verbose=-1))]),
        {"model__learning_rate": [0.03, 0.1], "model__max_depth": [3, 5]},
    ),
    "catboost": (
        Pipeline([("model", CatBoostClassifier(
            iterations=300, random_seed=RANDOM_STATE, verbose=0, allow_writing_files=False))]),
        {"model__learning_rate": [0.03, 0.1], "model__depth": [4, 6]},
    ),
    # Juan: la red neuronal necesita el escalado; con variables en escalas muy
    # distintas (edad al cuadrado frente a 0 o 1) aprende mal.
    "neural_net": (
        Pipeline([("scale", StandardScaler()),
                  ("model", MLPClassifier(
                      early_stopping=True, max_iter=500, random_state=RANDOM_STATE))]),
        {"model__hidden_layer_sizes": [(16,), (32, 16)], "model__alpha": [0.0001, 0.01]},
    ),
}


def calibration_line(y, p):
    """Intercepto y pendiente de una regresión logística de y sobre logit(p).

    Un modelo bien calibrado da intercepto cercano a 0 y pendiente cercana a 1.
    """
    p = np.clip(p, 1e-6, 1 - 1e-6)
    logit = np.log(p / (1 - p)).reshape(-1, 1)
    line = LogisticRegression(C=1e6).fit(logit, y)
    return line.intercept_[0], line.coef_[0][0]


SCORERS = {
    "auroc": "roc_auc",
    "auprc": "average_precision",
    "brier": make_scorer(brier_score_loss, response_method="predict_proba"),
    "calibration_intercept": make_scorer(
        lambda y, p: calibration_line(y, p)[0], response_method="predict_proba"),
    "calibration_slope": make_scorer(
        lambda y, p: calibration_line(y, p)[1], response_method="predict_proba"),
}


def split_data(table: pd.DataFrame):
    """Separa el 80 % para entrenar y el 20 % para la prueba final.

    Mantiene la misma proporción de ventas en las dos partes (estratificado)
    y usa RANDOM_STATE, para que todos trabajen con las mismas personas.
    """
    X, y = table.drop(columns=TARGET), table[TARGET]
    return train_test_split(X, y, test_size=0.2, stratify=y, random_state=RANDOM_STATE)


def compare_models(X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    """Compara los modelos de MODELS y devuelve una fila por modelo.

    Para cada modelo usa validación cruzada anidada: 3 particiones internas
    eligen los hiperparámetros y 5 externas miden el modelo con datos que no
    usó para elegirlos.
    """
    outer = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    inner = StratifiedKFold(3, shuffle=True, random_state=RANDOM_STATE)
    rows = []
    for name, (pipeline, grid) in MODELS.items():
        search = GridSearchCV(pipeline, grid, cv=inner, scoring="roc_auc", n_jobs=-1)
        scores = cross_validate(search, X_train, y_train, cv=outer, scoring=SCORERS)
        row = {"model": name}
        for metric in SCORERS:
            row[metric] = scores[f"test_{metric}"].mean()
            row[f"{metric}_sd"] = scores[f"test_{metric}"].std()
        rows.append(row)
        print(f"  {name}: AUROC {row['auroc']:.3f} ± {row['auroc_sd']:.3f}")
    return pd.DataFrame(rows)


def choose_winner(benchmark: pd.DataFrame) -> str:
    """Devuelve el nombre del modelo ganador según la regla del protocolo.

    Gana el de mayor AUROC promedio, salvo que un modelo más simple quede a
    menos de una desviación estándar del mejor: entonces gana el más simple.
    El orden de MODELS define cuál es más simple.
    """
    best = benchmark.loc[benchmark["auroc"].idxmax()]
    close_enough = benchmark[benchmark["auroc"] >= best["auroc"] - best["auroc_sd"]]
    return close_enough.iloc[0]["model"]


def evaluate_on_test(model, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
    """Mide al ganador en la prueba final, con intervalo de confianza para el AUROC."""
    p = model.predict_proba(X_test)[:, 1]
    rng = np.random.default_rng(RANDOM_STATE)
    samples = (rng.integers(0, len(p), len(p)) for _ in range(1000))
    boot = [roc_auc_score(y_test.iloc[i], p[i]) for i in samples]
    intercept, slope = calibration_line(y_test, p)
    return {
        "auroc": roc_auc_score(y_test, p),
        "auroc_ci95": list(np.percentile(boot, [2.5, 97.5])),
        "auprc": average_precision_score(y_test, p),
        "brier": brier_score_loss(y_test, p),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
    }


def export_model(model, metrics: dict) -> None:
    """Guarda el Pipeline ganador en models/ como .joblib y su metadata en .json."""
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODELS_DIR / "crash_reaction_v1.joblib")
    metadata = {**metrics, "trained_on": str(date.today()), "sklearn": sklearn.__version__}
    (MODELS_DIR / "crash_reaction_v1.json").write_text(
        json.dumps(metadata, indent=2, default=float), encoding="utf-8")


def main() -> None:
    """Ejecuta todo en orden: variables, partición, comparación, elección, prueba final y exportación."""
    if rebuild_features or not TRAINING_FILE.exists():
        print("Generando variables (etapa 2)...")
        build_training_table()  # escribe 
    table = pd.read_parquet(TRAINING_FILE)
    X_train, X_test, y_train, y_test = split_data(table)

    print("Comparando modelos (validación anidada 5 x 3)...")
    benchmark = compare_models(X_train, y_train)
    print(benchmark.round(3).to_string(index=False))

    winner = choose_winner(benchmark)
    pipeline, grid = MODELS[winner]
    inner = StratifiedKFold(3, shuffle=True, random_state=RANDOM_STATE)
    final = GridSearchCV(pipeline, grid, cv=inner, scoring="roc_auc").fit(X_train, y_train)

    metrics = {"winner": winner, "params": final.best_params_,
               "test": evaluate_on_test(final.best_estimator_, X_test, y_test)}
    print(f"Ganador: {winner} | prueba final: {metrics['test']}")
    export_model(final.best_estimator_, metrics)


if __name__ == "__main__":
    main()
