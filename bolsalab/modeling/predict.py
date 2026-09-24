"""Carga del modelo publicado y predicción. Es lo que importa el backend (FastAPI).

El backend nunca reimplementa el preprocesamiento: usa el imputer y el scaler
guardados dentro del artefacto joblib.

Ejemplo:
    from bolsalab.modeling.predict import PerfilModel
    modelo = PerfilModel("models/perfil_xgb_v1.joblib")
    modelo.predict({"capacidad_econ": 3, "horizonte": 5, ...})
"""

from pathlib import Path


class PerfilModel:
    def __init__(self, ruta_artefacto: str | Path):
        raise NotImplementedError

    def predict(self, respuestas: dict) -> dict:
        """Devuelve arquetipo, probabilidades por clase y las features con más peso (SHAP)."""
        raise NotImplementedError
