"""Etapas 4 y 5 del pipeline: entrenar, comparar, elegir y exportar.

1. Entrena los candidatos del clasificador de perfil: regresión logística,
   Random Forest, XGBoost y SVM lineal (split 70/15/15 estratificado).
2. Compara con F1 macro, recall por clase, calibración y costo asimétrico
   (predecir un perfil más agresivo que el real pesa el doble).
3. Valida el ganador con datos reales del SCF (pregunta X3014).
4. Exporta a models/:
   - perfil_<algoritmo>_v<n>.joblib con {model, imputer, scaler, explainer,
     features, classes}
   - perfil_<algoritmo>_v<n>_metadata.json con parámetros, métricas, split,
     hash del dataset y versiones de librerías.

Uso: python -m bolsalab.modeling.train
"""


def main() -> None:
    raise NotImplementedError


if __name__ == "__main__":
    main()
