"""Entrenamiento, comparación y exportación del modelo (etapa 3 del pipeline).

Es el paso donde el modelo aprende. Toma la tabla de entrenamiento de
features.py (54.704 personas, 17 variables y `sold`), entrena varios modelos,
los compara con las mismas reglas y guarda el ganador para que la API lo use.

Todas las reglas salen de docs/protocolo-evaluacion.md (secciones 4 a 7).

Corre en dos etapas, porque el 20 % de prueba se mira una sola vez:

    uv run python -m bolsalab.modeling.train              # compara los modelos
    uv run python -m bolsalab.modeling.train --final      # mide al ganador en la prueba
    uv run python -m bolsalab.modeling.train --prototype  # exporta sin mirar la prueba

La primera no toca la prueba y guarda la comparación en reports/benchmark.csv.
La segunda lee ese archivo, entrena al ganador y lo guarda en models/.
La tercera entrena al mismo ganador y lo guarda para la app, sin medirlo en la
prueba; --final lo reemplaza después con las métricas de prueba.
"""

import argparse
import json
from datetime import date

import joblib
import numpy as np
import pandas as pd
import sklearn
from catboost import CatBoostClassifier
from lightgbm import LGBMClassifier
from sklearn.base import clone
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, make_scorer, roc_auc_score
from sklearn.model_selection import (
    GridSearchCV,
    StratifiedKFold,
    cross_val_predict,
    cross_validate,
    train_test_split,
)
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from xgboost import XGBClassifier

from bolsalab.config import MODELS_DIR, RANDOM_STATE, REPORTS_DIR
from bolsalab.features import TRAINING_FILE
from bolsalab.features import main as build_training_table
from bolsalab.nfcs import match_brackets_by_position

# Las dos preguntas que la app todavía no hace (protocolo, sección 8).
NOT_ASKED = ["risk_aversion", "short_term_view"]
# Niveles de ingreso y activos que pregunta la app: bajo, medio bajo, medio, medio alto, alto.
APP_LEVELS = [1, 2, 3, 4, 5]

BENCHMARK_FILE = REPORTS_DIR / "benchmark.csv"
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


def evaluate_model(pipeline: Pipeline, grid: dict,
                   X_train: pd.DataFrame, y_train: pd.Series) -> dict:
    """Mide un modelo con validación cruzada anidada y devuelve sus métricas.

    3 particiones internas eligen los hiperparámetros y 5 externas miden el
    modelo con datos que no usó para elegirlos. Devuelve el promedio y la
    desviación estándar de cada métrica, y los hiperparámetros que eligió cada
    una de las 5 particiones externas. experiments.py usa esta misma función.
    """
    outer = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    inner = StratifiedKFold(3, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(pipeline, grid, cv=inner, scoring="roc_auc", n_jobs=-1)
    scores = cross_validate(search, X_train, y_train, cv=outer, scoring=SCORERS,
                            return_estimator=True)
    metrics = {}
    for metric in SCORERS:
        metrics[metric] = scores[f"test_{metric}"].mean()
        metrics[f"{metric}_sd"] = scores[f"test_{metric}"].std()
    metrics["best_params"] = json.dumps(
        [fold.best_params_ for fold in scores["estimator"]], default=str)
    return metrics


def compare_models(X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    """Compara los modelos de MODELS y devuelve una fila por modelo."""
    rows = []
    for name, (pipeline, grid) in MODELS.items():
        row = {"model": name, **evaluate_model(pipeline, grid, X_train, y_train)}
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


def category_cutoffs(model, X_train: pd.DataFrame, y_train: pd.Series) -> list[float]:
    """Cortes de las tres categorías de la app: percentiles 33,3 y 66,7.

    Cada persona del entrenamiento recibe la probabilidad de un modelo que no
    la vio (validación cruzada de 5 particiones). Protocolo, sección 8.
    """
    folds = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    p = cross_val_predict(clone(model), X_train, y_train, cv=folds, method="predict_proba")[:, 1]
    return [float(q) for q in np.quantile(p, [1 / 3, 2 / 3])]


def app_reference(X_train: pd.DataFrame) -> dict:
    """Valores que la app necesita del entrenamiento (protocolo, sección 8)."""
    levels = pd.Series(APP_LEVELS)
    return {
        "not_asked": {c: float(X_train[c].mode()[0]) for c in NOT_ASKED},
        "income_level_to_bracket": match_brackets_by_position(levels, X_train["income_bracket"]),
        "assets_level_to_bracket": match_brackets_by_position(levels, X_train["assets_bracket"]),
        "age_range": [int(X_train["age"].min()), int(X_train["age"].max())],
        "features": list(X_train.columns),
    }


def fit_winner(X_train: pd.DataFrame, y_train: pd.Series):
    """Entrena al ganador de reports/benchmark.csv con su rejilla, solo con el entrenamiento."""
    winner = choose_winner(pd.read_csv(BENCHMARK_FILE))
    pipeline, grid = MODELS[winner]
    inner = StratifiedKFold(3, shuffle=True, random_state=RANDOM_STATE)
    search = GridSearchCV(pipeline, grid, cv=inner, scoring="roc_auc").fit(X_train, y_train)
    return winner, search


def export_model(model, metrics: dict, X_train: pd.DataFrame, y_train: pd.Series) -> None:
    """Guarda el Pipeline ganador en models/ como .joblib y su metadata en .json."""
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODELS_DIR / "crash_reaction_v1.joblib")
    metadata = {**metrics, "trained_on": str(date.today()), "sklearn": sklearn.__version__,
                "base_rate": float(y_train.mean()),
                "cutoffs": category_cutoffs(model, X_train, y_train),
                **app_reference(X_train)}
    (MODELS_DIR / "crash_reaction_v1.json").write_text(
        json.dumps(metadata, indent=2, default=float), encoding="utf-8")


def run_benchmark(X_train: pd.DataFrame, y_train: pd.Series) -> None:
    """Etapa 1: compara los modelos y guarda la tabla. No toca la prueba."""
    print("Comparando modelos (validación anidada 5 x 3)...")
    benchmark = compare_models(X_train, y_train)
    print(benchmark.round(3).to_string(index=False))
    REPORTS_DIR.mkdir(exist_ok=True)
    benchmark.to_csv(BENCHMARK_FILE, index=False)
    print(f"Ganador según la regla del protocolo: {choose_winner(benchmark)}")
    print(f"Comparación guardada en {BENCHMARK_FILE}")


def run_final(X_train, X_test, y_train, y_test) -> None:
    """Etapa 2: entrena al ganador, lo mide una vez en la prueba y lo exporta."""
    winner, final = fit_winner(X_train, y_train)
    metrics = {"winner": winner, "params": final.best_params_,
               "test": evaluate_on_test(final.best_estimator_, X_test, y_test)}
    print(f"Ganador: {winner} | prueba final: {metrics['test']}")
    export_model(final.best_estimator_, metrics, X_train, y_train)


def run_prototype(X_train: pd.DataFrame, y_train: pd.Series) -> None:
    """Entrena al ganador y lo exporta para la app sin mirar la prueba."""
    winner, search = fit_winner(X_train, y_train)
    metrics = {"winner": winner, "params": search.best_params_, "test": None}
    print(f"Ganador: {winner} {search.best_params_} | exportado sin medir en la prueba")
    export_model(search.best_estimator_, metrics, X_train, y_train)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    stage = parser.add_mutually_exclusive_group()
    stage.add_argument("--final", action="store_true",
                       help="mide al ganador en la prueba (hacerlo una sola vez)")
    stage.add_argument("--prototype", action="store_true",
                       help="exporta al ganador para la app sin mirar la prueba")
    args = parser.parse_args()

    if not TRAINING_FILE.exists():
        print("No existe la tabla de entrenamiento; la genero con features.py...")
        build_training_table()
    X_train, X_test, y_train, y_test = split_data(pd.read_parquet(TRAINING_FILE))

    if args.final:
        run_final(X_train, X_test, y_train, y_test)
    elif args.prototype:
        run_prototype(X_train, y_train)
    else:
        run_benchmark(X_train, y_train)


if __name__ == "__main__":
    main()
