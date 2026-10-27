"""Desempeño del modelo por grupos: sexo, edad e ingreso.

Revisa si el modelo distingue y calibra peor para algún grupo. Usa las
predicciones de validación cruzada del entrenamiento (5 particiones, semilla
42): cada persona recibe la probabilidad de un modelo que no la vio. No toca
el 20 % de prueba.

    uv run python -m bolsalab.modeling.groups

Guarda la tabla en reports/groups.csv.
"""

import joblib
import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from bolsalab.config import MODELS_DIR, RANDOM_STATE, REPORTS_DIR
from bolsalab.features import TRAINING_FILE
from bolsalab.modeling.train import calibration_line, split_data

GROUPS_FILE = REPORTS_DIR / "groups.csv"


def group_labels(X: pd.DataFrame) -> dict[str, pd.Series]:
    """Etiqueta de cada persona en los tres cortes que revisamos."""
    return {
        "Sexo": pd.Series(np.where(X["male"] == 1, "Hombres", "Mujeres"), index=X.index),
        "Edad": pd.cut(X["age"], [0, 39, 59, 200],
                       labels=["18 a 39", "40 a 59", "60 o más"]).astype(str),
        "Ingreso": pd.cut(X["income_bracket"], [0, 4, 7, 100],
                          labels=["Tramos 1 a 4", "Tramos 5 a 7", "Tramos 8 o más"]).astype(str),
    }


def performance_by_group(model, X_train: pd.DataFrame, y_train: pd.Series) -> pd.DataFrame:
    folds = StratifiedKFold(5, shuffle=True, random_state=RANDOM_STATE)
    p = cross_val_predict(clone(model), X_train, y_train, cv=folds, method="predict_proba")[:, 1]
    p = pd.Series(p, index=X_train.index)
    rows = []
    for group, labels in group_labels(X_train).items():
        for value in sorted(labels.unique()):
            m = labels == value
            intercept, slope = calibration_line(y_train[m].to_numpy(), p[m].to_numpy())
            rows.append({"grupo": group, "valor": value, "personas": int(m.sum()),
                         "vendio": y_train[m].mean(), "prediccion_media": p[m].mean(),
                         "auroc": roc_auc_score(y_train[m], p[m]),
                         "calibration_intercept": intercept, "calibration_slope": slope})
    return pd.DataFrame(rows)


def main() -> None:
    X_train, _, y_train, _ = split_data(pd.read_parquet(TRAINING_FILE))
    model = joblib.load(MODELS_DIR / "crash_reaction_v1.joblib")
    table = performance_by_group(model, X_train, y_train)
    print(table.round(3).to_string(index=False))
    table.to_csv(GROUPS_FILE, index=False)
    print(f"Tabla guardada en {GROUPS_FILE}")


if __name__ == "__main__":
    main()
