"""Registra en MLflow el modelo que exportó train.py.

Lee los archivos que dejó el entrenamiento en models/ (el paquete .joblib y su
.json) y crea una corrida en el experimento del modelo final, con la hora real
del entrenamiento. Con "final", además registra el modelo en el registro de
MLflow como una versión nueva.

Como lee de los archivos, sirve también para subir después una corrida a otro
servidor (AWS) sin volver a entrenar ni a medir la prueba. Si la corrida ya
existe en ese servidor, no la duplica.

No registra datos de personas: solo parámetros, métricas y el modelo.

train.py la llama sola al terminar --prototype y --final. Para registrar a mano
el modelo que está en models/ (por ejemplo, si MLflow falló al entrenar):

    uv run python -m bolsalab.modeling.mlflow_tracking final
"""

import argparse
import json
from datetime import datetime
from pathlib import Path

import joblib
import mlflow
from mlflow.tracking import MlflowClient

from bolsalab.config import (MLFLOW_EXPERIMENTS, MLFLOW_REGISTERED_MODEL, MLFLOW_TRACKING_URI,
                             MODELS_DIR)
from bolsalab.modeling.groups import GROUPS_TEST_FILE
from bolsalab.modeling.mlflow_backfill import experiment_id

ARTIFACT_NAME = "crash_reaction_v1"
# MLflow guarda los modelos con skops, que solo acepta las clases que se declaran
# confiables. Estas son las que usa el modelo final: la nuestra y las de XGBoost.
TRUSTED_TYPES = ["bolsalab.modeling.early_stopping.EarlyStoppingBooster",
                 "xgboost.core.Booster", "xgboost.sklearn.XGBClassifier"]


def run_params(meta: dict) -> dict:
    """Configuración, hiperparámetros elegidos, partición y versiones."""
    params = {"configuracion": meta["winner"]}
    # "model__estimator__gamma" queda como "gamma"
    params.update({name.split("__")[-1]: value for name, value in meta["params"].items()})
    params.update(meta["split"])
    params.update({f"version_{lib}": v for lib, v in meta["versions"].items()})
    params["cortes_app"] = meta["cutoffs"]
    return params


def run_metrics(meta: dict) -> dict:
    """Métricas de la prueba (solo en la final) y de la validación cruzada, para comparar."""
    metrics = {f"cv_{name}": value for name, value in meta["cv_estimate"].items()}
    test = meta.get("test") or {}
    for name, value in test.items():
        if name == "auroc_ci95":
            metrics["test_auroc_ci95_bajo"], metrics["test_auroc_ci95_alto"] = value
        else:
            metrics[f"test_{name}"] = value
    return metrics


def log_exported_model(kind: str, models_dir: Path = MODELS_DIR,
                       tracking_uri: str = MLFLOW_TRACKING_URI,
                       groups_file: Path = GROUPS_TEST_FILE) -> str:
    """Registra el modelo exportado y devuelve el id de su corrida.

    kind es "prototipo" o "final". Solo "final" crea una versión en el registro.
    """
    package = models_dir / f"{ARTIFACT_NAME}.joblib"
    metadata = models_dir / f"{ARTIFACT_NAME}.json"
    meta = json.loads(metadata.read_text(encoding="utf-8"))

    client = MlflowClient(tracking_uri)
    exp_id = experiment_id(client, MLFLOW_EXPERIMENTS["final"], tracking_uri)
    # Si esta corrida ya está en el servidor (mismo tipo y misma hora), no se duplica.
    found = client.search_runs([exp_id], filter_string=(
        f"tags.tipo = '{kind}' and tags.trained_at = '{meta['trained_at']}'"))
    if found:
        return found[0].info.run_id

    start = int(datetime.fromisoformat(meta["trained_at"]).timestamp() * 1000)
    tags = {"tipo": kind, "trained_at": meta["trained_at"], "git_commit": str(meta["git"]["commit"]),
            "uncommitted_changes": str(meta["git"]["uncommitted_changes"]),
            "dataset_sha256": meta["dataset_sha256"]}
    run_id = client.create_run(exp_id, start_time=start, tags=tags, run_name=kind).info.run_id
    # Si algo falla a mitad de camino, la corrida se borra: así el reintento
    # empieza limpio y no deja una corrida "final" sin su versión del modelo.
    try:
        for name, value in run_params(meta).items():
            client.log_param(run_id, name, value)
        for name, value in run_metrics(meta).items():
            client.log_metric(run_id, name, float(value))
        client.log_artifact(run_id, str(package))
        client.log_artifact(run_id, str(metadata))
        if kind == "final" and groups_file.exists():
            client.log_artifact(run_id, str(groups_file))
        if kind == "final":
            # El registro de modelos necesita el modelo en el formato de MLflow.
            mlflow.set_tracking_uri(tracking_uri)
            with mlflow.start_run(run_id=run_id):
                info = mlflow.sklearn.log_model(joblib.load(package)["model"], name="modelo",
                                                skops_trusted_types=TRUSTED_TYPES)
        client.set_terminated(run_id, end_time=start)
        # La versión del modelo se crea al final, cuando todo lo demás ya quedó.
        if kind == "final":
            mlflow.register_model(info.model_uri, MLFLOW_REGISTERED_MODEL)
    except Exception:
        client.delete_run(run_id)
        raise
    return run_id


def main() -> None:
    parser = argparse.ArgumentParser(description="Registra en MLflow el modelo de models/.")
    parser.add_argument("kind", choices=["prototipo", "final"])
    run_id = log_exported_model(parser.parse_args().kind)
    print(f"Registrado en MLflow: corrida {run_id} en {MLFLOW_TRACKING_URI}")


if __name__ == "__main__":
    main()
