"""Explicación global del modelo con SHAP.

Responde qué variables pesan más en las predicciones y hacia dónde empujan.
Usa una muestra del entrenamiento: el 20 % de prueba no se toca.

Guarda solo resultados agregados, que la app muestra sin cargar datos:

- reports/shap_global.csv: peso medio de cada variable y su dirección;
- reports/figures/shap_importancia.png y shap_beeswarm.png.

SHAP explica lo que hace el modelo, no la causa de la venta.

Uso: uv run python -m bolsalab.explain
"""

import matplotlib.pyplot as plt
import pandas as pd
import shap

from bolsalab.config import FIGURES_DIR, RANDOM_STATE, REPORTS_DIR
from bolsalab.features import TRAINING_FILE
from bolsalab.modeling.predict import CrashReactionModel
from bolsalab.modeling.train import split_data

SAMPLE_SIZE = 5000
GLOBAL_FILE = REPORTS_DIR / "shap_global.csv"

NAMES = {
    "knows_interest": "Acierta interés compuesto",
    "knows_inflation": "Acierta inflación",
    "knows_diversification": "Acierta diversificación",
    "knowledge_confidence": "Confianza en lo que sabe",
    "overconfidence": "Exceso de confianza",
    "age": "Edad",
    "male": "Hombre",
    "university": "Título universitario",
    "married": "Casado(a)",
    "has_children": "Tiene hijos",
    "urban": "Vive en ciudad grande",
    "employed": "Tiene empleo",
    "risk_aversion": "Aversión al riesgo",
    "short_term_view": "Visión de corto plazo",
    "income_bracket": "Tramo de ingreso",
    "assets_bracket": "Tramo de ahorros e inversiones",
}


def join_age(values: pd.DataFrame) -> pd.DataFrame:
    """Suma el aporte de edad² al de edad: son la misma pregunta."""
    values = values.copy()
    values["age"] += values.pop("age_squared")
    return values


def global_table(values: pd.DataFrame, X: pd.DataFrame) -> pd.DataFrame:
    """Peso medio (|SHAP| promedio), su parte del total y hacia dónde empuja la variable.

    La dirección es la correlación entre el valor de la variable y su aporte:
    positiva si valores más altos suben la propensión a vender.
    """
    weight = values.abs().mean()
    direction = pd.Series({c: values[c].corr(X[c]) for c in values.columns})
    table = pd.DataFrame({
        "variable": weight.index,
        "nombre": [NAMES[c] for c in weight.index],
        "peso_medio": weight.values,
        "parte_del_total": (weight / weight.sum()).values,
        "direccion": direction[weight.index].values,
    })
    return table.sort_values("peso_medio", ascending=False).reset_index(drop=True)


def main() -> None:
    model = CrashReactionModel()
    X_train, _, _, _ = split_data(pd.read_parquet(TRAINING_FILE))
    sample = X_train.sample(SAMPLE_SIZE, random_state=RANDOM_STATE)
    explanation = model.explainer(sample)

    values = join_age(pd.DataFrame(explanation.values, columns=sample.columns))
    shown = sample.drop(columns="age_squared").reset_index(drop=True)
    table = global_table(values, shown)
    table.to_csv(GLOBAL_FILE, index=False)
    print(table.round(3).to_string(index=False))

    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    order = table["variable"][::-1]
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.barh([NAMES[c] for c in order], table.set_index("variable").loc[order, "peso_medio"],
            color="#1F67BF")
    ax.set_xlabel("Peso medio en la predicción (|SHAP|, escala log-odds)")
    ax.set_title("Qué respuestas pesan más en el modelo")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "shap_importancia.png", dpi=150)
    plt.close(fig)

    joined = shap.Explanation(values.values, data=shown.values,
                              feature_names=[NAMES[c] for c in shown.columns])
    shap.plots.beeswarm(joined, max_display=16, show=False)
    fig = plt.gcf()
    fig.set_size_inches(8, 6)
    main_ax, color_ax = fig.axes[0], fig.axes[-1]
    main_ax.set_xlabel("Aporte SHAP (log-odds): a la derecha sube la venta")
    main_ax.set_title("Cada punto es una persona")
    color_ax.set_ylabel("Valor de la respuesta")
    color_ax.set_yticklabels(["Bajo", "Alto"])
    plt.tight_layout()
    plt.savefig(FIGURES_DIR / "shap_beeswarm.png", dpi=150)
    plt.close("all")
    print(f"Guardado en {GLOBAL_FILE} y {FIGURES_DIR}")


if __name__ == "__main__":
    main()
