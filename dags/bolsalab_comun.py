"""Ajustes compartidos por los flujos de BolsaLAB en Airflow."""

import os
from datetime import datetime, timedelta

# Raíz del repositorio. Se define al arrancar Airflow: export BOLSALAB_DIR=/ruta/a/bolsalab
if "BOLSALAB_DIR" not in os.environ:
    raise RuntimeError("Falta la variable BOLSALAB_DIR con la ruta del repositorio")
REPO = os.environ["BOLSALAB_DIR"]

# uv corre cada etapa en el entorno del proyecto (uv.lock), no en el de Airflow.
UV = os.environ.get("BOLSALAB_UV", "uv")
RUN = f'cd "{REPO}" && {UV} run python -m '
PYTEST = f'cd "{REPO}" && {UV} run pytest -q '

# Python del entorno del proyecto, para las tareas escritas como funciones.
PROJECT_PYTHON = f"{REPO}/.venv/bin/python"

# Variables que reciben las etapas, además de las del sistema.
ENV = {
    "MLFLOW_TRACKING_URI": os.environ.get("MLFLOW_TRACKING_URI", f"sqlite:///{REPO}/mlflow.db"),
}

DEFAULT_ARGS = {
    "owner": "grupo-10",
    "retries": 0,
    "execution_timeout": timedelta(hours=2),
}

START_DATE = datetime(2026, 11, 1)

# Código de salida con el que una etapa se marca como "saltada" y no como "fallida".
SKIP = 99

# Revisa si el modelo de models/ ya fue medido en la prueba. Sale con 99 si es así.
GUARD_FINAL_MODEL = (
    "import json, sys; "
    "from bolsalab.config import MODELS_DIR, MODEL_ARTIFACT_NAME; "
    "p = MODELS_DIR / f'{MODEL_ARTIFACT_NAME}.json'; "
    "sys.exit(99 if p.exists() and json.loads(p.read_text()).get('test') else 0)"
)
