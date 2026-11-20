"""Registra en MLflow el modelo que exportó train.py.

Lee los archivos que dejó el entrenamiento en models/ (el paquete .joblib y su
.json) y crea una corrida en el experimento del modelo final, con la hora real
del entrenamiento. El tipo de corrida sale del .json: si trae resultados de
la prueba es "final" y además registra el modelo en el registro de MLflow como
una versión nueva; si no, es "prototipo".

Como lee de los archivos, sirve también para subir después una corrida a otro
servidor (AWS) sin volver a entrenar ni a medir la prueba. Si la corrida ya
existe en ese servidor, no la duplica.

No registra datos de personas: solo parámetros, métricas y el modelo.

train.py la llama sola al terminar --prototype y --final. Para registrar a mano
el modelo que está en models/ (por ejemplo, si MLflow falló al entrenar):

    uv run python -m bolsalab.modeling.mlflow_tracking
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import joblib
import mlflow
from mlflow.tracking import MlflowClient

from bolsalab.config import (MLFLOW_EXPERIMENTS, MLFLOW_REGISTERED_MODEL, MLFLOW_TRACKING_URI,
                             MODEL_ARTIFACT_NAME, MODELS_DIR)
from bolsalab.modeling.mlflow_backfill import experiment_id

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


def log_mlflow_model(client: MlflowClient, run_id: str, package: Path) -> None:
    """Sube el modelo en el formato de MLflow, que es el que usa el registro de modelos."""
    with tempfile.TemporaryDirectory() as folder:
        # pyfunc_predict_fn: quien lo cargue desde el registro recibe probabilidades, no 0 o 1.
        mlflow.sklearn.save_model(joblib.load(package)["model"], f"{folder}/modelo",
                                  skops_trusted_types=TRUSTED_TYPES, pyfunc_predict_fn="predict_proba")
        client.log_artifacts(run_id, f"{folder}/modelo", "modelo")


def register_version(client: MlflowClient, run_id: str) -> None:
    """Crea una versión nueva del modelo en el registro, con el modelo de la corrida."""
    if not client.search_registered_models(f"name = '{MLFLOW_REGISTERED_MODEL}'"):
        client.create_registered_model(MLFLOW_REGISTERED_MODEL)
    source = f"{client.get_run(run_id).info.artifact_uri}/modelo"
    client.create_model_version(MLFLOW_REGISTERED_MODEL, source, run_id)


def log_exported_model(models_dir: Path = MODELS_DIR,
                       tracking_uri: str = MLFLOW_TRACKING_URI) -> str:
    """Registra el modelo exportado y devuelve el id de su corrida."""
    package = models_dir / f"{MODEL_ARTIFACT_NAME}.joblib"
    metadata = models_dir / f"{MODEL_ARTIFACT_NAME}.json"
    meta = json.loads(metadata.read_text(encoding="utf-8"))
    if "trained_at" not in meta:
        raise ValueError("Este modelo se exportó antes de guardar la hora del entrenamiento; "
                         "vuelve a exportarlo con: uv run python -m bolsalab.modeling.train --prototype")
    # Solo --final mide la prueba, así que un prototipo nunca puede quedar como versión del modelo.
    kind = "final" if meta.get("test") else "prototipo"

    client = MlflowClient(tracking_uri)
    exp_id = experiment_id(client, MLFLOW_EXPERIMENTS["final"], tracking_uri)
    # Si esta corrida ya está completa en el servidor (mismo tipo y misma hora), no se duplica.
    # Las que quedaron a medias de un intento anterior se borran y se hace de nuevo.
    found = client.search_runs([exp_id], filter_string=(
        f"tags.tipo = '{kind}' and tags.trained_at = '{meta['trained_at']}'"))
    complete = [run for run in found if run.data.tags.get("completa") == "si"]
    if complete:
        return complete[0].info.run_id
    for run in found:
        client.delete_run(run.info.run_id)

    start = int(datetime.fromisoformat(meta["trained_at"]).timestamp() * 1000)
    tags = {"tipo": kind, "trained_at": meta["trained_at"], "git_commit": str(meta["git"]["commit"]),
            "uncommitted_changes": str(meta["git"]["uncommitted_changes"]),
            "dataset_sha256": meta["dataset_sha256"]}
    run_id = client.create_run(exp_id, start_time=start, tags=tags, run_name=kind).info.run_id
    # Si algo falla a mitad de camino (también con Ctrl+C), la corrida se borra
    # para que el reintento empiece limpio. La etiqueta "completa" se pone al
    # final: una corrida sin ella nunca cuenta como hecha.
    try:
        for name, value in run_params(meta).items():
            client.log_param(run_id, name, value)
        for name, value in run_metrics(meta).items():
            client.log_metric(run_id, name, float(value))
        client.log_artifact(run_id, str(package))
        client.log_artifact(run_id, str(metadata))
        if kind == "final":
            # Los grupos de la prueba salen del mismo .json, así que son de este entrenamiento.
            client.log_dict(run_id, meta["test_groups"], "groups_test.json")
            log_mlflow_model(client, run_id, package)
        client.set_terminated(run_id, end_time=start)
        if kind == "final":
            # La versión del modelo se crea al final, cuando todo lo demás ya quedó.
            register_version(client, run_id)
        client.set_tag(run_id, "completa", "si")
    except BaseException:
        client.delete_run(run_id)
        raise
    return run_id


def main() -> None:
    run_id = log_exported_model()
    print(f"Registrado en MLflow: corrida {run_id} en {MLFLOW_TRACKING_URI}")


if __name__ == "__main__":
    main()
