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
La segunda entrena la configuración final (FINAL_MODEL, elegida en el protocolo,
sección 7, después del ajuste por familias), la mide una vez en la prueba y la
guarda en models/. La tercera entrena esa misma configuración y la guarda para la
app, sin medirla en la prueba; --final la reemplaza después con las métricas.
"""

import argparse
import hashlib
import json
import platform
import subprocess
from datetime import date

import joblib
import numpy as np
import pandas as pd
import shap
import sklearn
import xgboost
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

from bolsalab.config import MODELS_DIR, PROJ_ROOT, RANDOM_STATE, REPORTS_DIR
from bolsalab.features import TRAINING_FILE
from bolsalab.features import main as build_training_table
from bolsalab.modeling.optuna_search import OptunaSearch
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
                   X_train: pd.DataFrame, y_train: pd.Series,
                   overfit_gap: bool = False, fold_detail=None,
                   n_trials: int | None = None, fit_params: dict | None = None) -> dict:
    """Mide un modelo con validación cruzada anidada y devuelve sus métricas.

    3 particiones internas eligen los hiperparámetros y 5 externas miden el
    modelo con datos que no usó para elegirlos. Devuelve el promedio y la
    desviación estándar de cada métrica, y los hiperparámetros que eligió cada
    una de las 5 particiones externas. experiments.py usa esta misma función.

    Con overfit_gap=True agrega el AUROC sobre las personas con las que entrenó
    cada partición y la brecha frente al de validación: si la brecha crece, el
    modelo está memorizando. Viene apagado para que benchmark.csv y
    experiments.csv conserven sus columnas.

    fold_detail es una función opcional que recibe el modelo ganador de cada
    partición externa y devuelve un dato para guardar, por ejemplo cuántos
    árboles usó con parada temprana.

    Con n_trials, los hiperparámetros los busca Optuna en vez de la rejilla:
    grid trae rangos (mínimo y máximo) en lugar de listas, y Optuna prueba
    n_trials combinaciones en cada partición externa (optuna_search.py). La
    validación 5 x 3 y las métricas son las mismas.

    fit_params son datos extra que el modelo recibe solo al entrenar, una fila
    por persona y en el mismo orden que X_train. scikit-learn los recorta en
    cada partición. Lo usa la prueba de tres clases (tuning.py, paso 10).
    Solo funcionan con la rejilla: OptunaSearch no los recibe.
    """
    if fit_params and n_trials is not None:
        raise ValueError("fit_params solo funciona con la rejilla, no con Optuna")
    outer = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    inner = StratifiedKFold(3, shuffle=True, random_state=RANDOM_STATE)
    if n_trials is None:
        search = GridSearchCV(pipeline, grid, cv=inner, scoring="roc_auc", n_jobs=-1)
    else:
        search = OptunaSearch(pipeline, grid, n_trials=n_trials, cv=inner)
    scores = cross_validate(search, X_train, y_train, cv=outer, scoring=SCORERS,
                            return_estimator=True, return_train_score=overfit_gap,
                            params=fit_params)
    metrics = {}
    for metric in SCORERS:
        metrics[metric] = scores[f"test_{metric}"].mean()
        metrics[f"{metric}_sd"] = scores[f"test_{metric}"].std()
    if overfit_gap:
        metrics["train_auroc"] = scores["train_auroc"].mean()
        metrics["overfit_gap"] = (scores["train_auroc"] - scores["test_auroc"]).mean()
    metrics["best_params"] = json.dumps(
        [fold.best_params_ for fold in scores["estimator"]], default=str)
    if fold_detail is not None:
        metrics["fold_detail"] = json.dumps(
            [fold_detail(fold.best_estimator_) for fold in scores["estimator"]], default=str)
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
    # El 10 % de personas con la probabilidad más alta: qué parte de ellas vendió.
    top = np.argsort(-p)[: int(np.ceil(len(p) / 10))]
    return {
        "auroc": roc_auc_score(y_test, p),
        "auroc_ci95": list(np.percentile(boot, [2.5, 97.5])),
        "auprc": average_precision_score(y_test, p),
        "brier": brier_score_loss(y_test, p),
        "calibration_intercept": intercept,
        "calibration_slope": slope,
        "sold_rate": float(y_test.mean()),
        "sold_rate_top10": float(y_test.iloc[top].mean()),
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


# Configuración final (protocolo, sección 7): el XGBoost con parada temprana y poda
# del paso 2 del ajuste por familias, con su misma rejilla.
FINAL_MODEL = "xgboost|poda"


def final_search() -> GridSearchCV:
    """La configuración final sin entrenar: el modelo y su rejilla con 3 particiones.

    La usan fit_winner (entrenamiento final) y groups.py (desempeño por grupos).
    """
    # tuning.py importa este módulo; por eso se importa aquí y no arriba.
    from bolsalab.modeling.tuning import xgboost_with_pruning
    pipeline, grid = xgboost_with_pruning()
    inner = StratifiedKFold(3, shuffle=True, random_state=RANDOM_STATE)
    return GridSearchCV(pipeline, grid, cv=inner, scoring="roc_auc", n_jobs=-1)


def fit_winner(X_train: pd.DataFrame, y_train: pd.Series):
    """Entrena la configuración final con su rejilla, solo con el entrenamiento."""
    return FINAL_MODEL, final_search().fit(X_train, y_train)


def git_state() -> dict:
    """Commit con el que se entrenó y si había cambios sin guardar en el código.

    No cuenta models/ ni reports/, que los escribe el mismo entrenamiento, ni
    los archivos que no están en git.
    """
    def git(*args):
        return subprocess.run(["git", *args], cwd=PROJ_ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
    try:
        changes = git("status", "--porcelain", "--untracked-files=no", "--",
                      ".", ":!models", ":!reports")
        return {"commit": git("rev-parse", "HEAD"), "uncommitted_changes": bool(changes)}
    except (OSError, subprocess.CalledProcessError):
        return {"commit": None, "uncommitted_changes": None}


def cv_estimate() -> dict:
    """Lo que dio la configuración final en la validación cruzada, para compararlo con la prueba."""
    # tuning.py importa este módulo; por eso se importa aquí y no arriba.
    from bolsalab.modeling.tuning import TUNING_FILE
    results = pd.read_csv(TUNING_FILE).drop_duplicates("experiment", keep="last")
    row = results.set_index("experiment").loc[FINAL_MODEL]
    return {k: float(row[k]) for k in ["auroc", "auroc_sd", "calibration_slope", "overfit_gap"]}


def traceability(y_train: pd.Series, y_test: pd.Series) -> dict:
    """Con qué datos, partición, código y versiones se entrenó el modelo."""
    return {
        "dataset_sha256": hashlib.sha256(TRAINING_FILE.read_bytes()).hexdigest(),
        "split": {"test_size": 0.2, "random_state": RANDOM_STATE,
                  "train_rows": len(y_train), "test_rows": len(y_test),
                  "train_sold_rate": float(y_train.mean()), "test_sold_rate": float(y_test.mean())},
        "versions": {"python": platform.python_version(), "sklearn": sklearn.__version__,
                     "xgboost": xgboost.__version__, "shap": shap.__version__,
                     "numpy": np.__version__, "pandas": pd.__version__},
        "git": git_state(),
        "preprocessing": "Ninguno: XGBoost no necesita escalado y la tabla no tiene datos faltantes",
        "cv_estimate": cv_estimate(),
    }


def export_model(model, metrics: dict, X_train: pd.DataFrame, y_train: pd.Series,
                 y_test: pd.Series) -> None:
    """Guarda el modelo en models/: el paquete en .joblib y su metadata en .json.

    El paquete trae todo lo que necesita quien lo cargue: el Pipeline, el
    explicador SHAP ya armado, las variables en orden y las clases.
    """
    MODELS_DIR.mkdir(exist_ok=True)
    # Con parada temprana, el XGBoost va dentro del envoltorio (estimator_).
    trees = getattr(model[-1], "estimator_", model[-1])
    artifact = {"model": model, "explainer": shap.TreeExplainer(trees),
                "features": list(X_train.columns), "classes": [int(c) for c in model.classes_]}
    joblib.dump(artifact, MODELS_DIR / "crash_reaction_v1.joblib")
    metadata = {**metrics, "trained_on": str(date.today()),
                "base_rate": float(y_train.mean()),
                "cutoffs": category_cutoffs(model, X_train, y_train),
                **traceability(y_train, y_test),
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
    """Etapa 2: entrena la configuración final, la mide una vez en la prueba y la exporta."""
    # groups.py importa este módulo; por eso se importa aquí y no arriba.
    from bolsalab.modeling.groups import GROUPS_TEST_FILE, table_by_group
    winner, final = fit_winner(X_train, y_train)
    model = final.best_estimator_
    groups = table_by_group(X_test, y_test, model.predict_proba(X_test)[:, 1])
    metrics = {"winner": winner, "params": final.best_params_,
               "test": evaluate_on_test(model, X_test, y_test),
               "test_groups": groups.to_dict("records")}
    print(f"Ganador: {winner} | prueba final: {metrics['test']}")
    print(groups.round(3).to_string(index=False))
    groups.to_csv(GROUPS_TEST_FILE, index=False)
    export_model(model, metrics, X_train, y_train, y_test)


def run_prototype(X_train, y_train, y_test) -> None:
    """Entrena la configuración final y la exporta para la app sin mirar la prueba.

    y_test solo se usa para anotar el tamaño de la partición en la metadata.
    """
    winner, search = fit_winner(X_train, y_train)
    metrics = {"winner": winner, "params": search.best_params_, "test": None}
    print(f"Ganador: {winner} {search.best_params_} | exportado sin medir en la prueba")
    export_model(search.best_estimator_, metrics, X_train, y_train, y_test)


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
        run_prototype(X_train, y_train, y_test)
    else:
        run_benchmark(X_train, y_train)


if __name__ == "__main__":
    main()
