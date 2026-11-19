"""Desempeño del modelo por grupos: sexo, edad, ingreso y principiantes.

Revisa si el modelo distingue y calibra peor para algún grupo. Usa la
configuración final (train.final_search) y sus predicciones de validación
cruzada del entrenamiento (5 particiones, semilla 42): cada persona recibe la
probabilidad de un modelo que no la vio, y cada partición elige sus
hiperparámetros por su cuenta. No toca el 20 % de prueba.

"Principiantes" es el grupo más parecido al usuario de la app: menores de 35
años que acertaron 0 o 1 de las tres preguntas de finanzas.

    uv run python -m bolsalab.modeling.groups

Guarda la tabla en reports/groups.csv.
"""

import numpy as np
import pandas as pd
from sklearn.base import clone
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold, cross_val_predict

from bolsalab.config import RANDOM_STATE, REPORTS_DIR
from bolsalab.features import TRAINING_FILE
from bolsalab.modeling.train import calibration_line, final_search, split_data
from bolsalab.modeling.transformers import QUESTIONS

GROUPS_FILE = REPORTS_DIR / "groups.csv"

# Principiante: menos de 35 años y 0 o 1 aciertos de 3 (decisión nuestra, protocolo sección 7).
BEGINNER_AGE_UNDER = 35
BEGINNER_CORRECT_UP_TO = 1


def group_labels(X: pd.DataFrame) -> dict[str, pd.Series]:
    """Etiqueta de cada persona en los cortes que revisamos."""
    beginner = (X["age"] < BEGINNER_AGE_UNDER) & (X[QUESTIONS].sum(axis=1) <= BEGINNER_CORRECT_UP_TO)
    return {
        "Sexo": pd.Series(np.where(X["male"] == 1, "Hombres", "Mujeres"), index=X.index),
        "Edad": pd.cut(X["age"], [0, 39, 59, 200],
                       labels=["18 a 39", "40 a 59", "60 o más"]).astype(str),
        "Ingreso": pd.cut(X["income_bracket"], [0, 4, 7, 100],
                          labels=["Tramos 1 a 4", "Tramos 5 a 7", "Tramos 8 o más"]).astype(str),
        "Principiantes": pd.Series(np.where(beginner, "Sí", "No"), index=X.index),
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
    table = performance_by_group(final_search(), X_train, y_train)
    print(table.round(3).to_string(index=False))
    table.to_csv(GROUPS_FILE, index=False)
    print(f"Tabla guardada en {GROUPS_FILE}")


if __name__ == "__main__":
    main()
