"""Pruebas del registro en MLflow del modelo exportado.

Usan un modelo pequeño con datos inventados, una carpeta temporal y un MLflow
temporal. No tocan models/, el mlflow.db del proyecto ni el 20 % de prueba.
"""

import json
import shutil
from datetime import datetime

import numpy as np
import pandas as pd
import pytest
from mlflow.tracking import MlflowClient
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from bolsalab.config import MLFLOW_EXPERIMENTS, MLFLOW_REGISTERED_MODEL
from bolsalab.modeling import mlflow_tracking, train
from bolsalab.modeling.early_stopping import EarlyStoppingBooster
from bolsalab.modeling.mlflow_tracking import log_exported_model

# Resultados de prueba inventados, solo para recorrer el camino de "final".
FAKE_TEST = {"auroc": 0.66, "auroc_ci95": [0.65, 0.67], "auprc": 0.33, "brier": 0.15,
             "calibration_intercept": 0.0, "calibration_slope": 1.0,
             "sold_rate": 0.2, "sold_rate_top10": 0.35}


@pytest.fixture(scope="module")
def exported(tmp_path_factory):
    """Un modelo pequeño con parada temprana, exportado igual que lo hace train.py."""
    rng = np.random.default_rng(0)
    n = 600
    age = rng.integers(18, 80, n)
    X = pd.DataFrame({"signal": rng.normal(size=n), "age": age, "age_squared": age ** 2,
                      "income_bracket": rng.integers(1, 13, n), "assets_bracket": rng.integers(1, 11, n),
                      "risk_aversion": rng.integers(0, 11, n) / 10, "short_term_view": rng.integers(1, 6, n)})
    y = pd.Series((rng.random(n) < 1 / (1 + np.exp(1.5 - X["signal"]))).astype(int))
    folder = tmp_path_factory.mktemp("models")
    table = folder / "tabla.parquet"
    X.assign(sold=y).to_parquet(table)
    model = Pipeline([("model", EarlyStoppingBooster(XGBClassifier(n_estimators=100), patience=10))]).fit(X, y)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(train, "MODELS_DIR", folder)
        mp.setattr(train, "TRAINING_FILE", table)
        train.export_model(model, {"winner": "xgboost|poda", "params": {"model__estimator__gamma": 0.5},
                                   "test": None}, X, y, y.iloc[:150])
    return folder


@pytest.fixture
def final_folder(exported, tmp_path):
    """Copia del modelo exportado con resultados de prueba, como lo deja --final."""
    folder = tmp_path / "final"
    shutil.copytree(exported, folder)
    path = folder / "crash_reaction_v1.json"
    meta = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps({**meta, "test": FAKE_TEST}), encoding="utf-8")
    return folder


@pytest.fixture
def uri(tmp_path):
    return f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}"


def versions(uri):
    return MlflowClient(uri).search_model_versions(f"name='{MLFLOW_REGISTERED_MODEL}'")


def test_prototype_logs_a_run_without_a_model_version(exported, uri, tmp_path):
    run_id = log_exported_model("prototipo", exported, uri, tmp_path / "sin_grupos.csv")
    run = MlflowClient(uri).get_run(run_id)
    assert run.data.tags["tipo"] == "prototipo"
    assert run.data.params["configuracion"] == "xgboost|poda"
    assert run.data.params["gamma"] == "0.5"
    assert "cv_auroc" in run.data.metrics
    assert not any(name.startswith("test_") for name in run.data.metrics)
    assert versions(uri) == []


def test_final_logs_test_metrics_files_and_version_one(final_folder, uri, tmp_path):
    groups = tmp_path / "groups_test.csv"
    pd.DataFrame({"grupo": ["Sexo"], "auroc": [0.6]}).to_csv(groups, index=False)
    run_id = log_exported_model("final", final_folder, uri, groups)
    client = MlflowClient(uri)
    run = client.get_run(run_id)
    assert run.data.metrics["test_auroc"] == pytest.approx(0.66)
    assert run.data.metrics["test_auroc_ci95_bajo"] == pytest.approx(0.65)
    files = {artifact.path for artifact in client.list_artifacts(run_id)}
    assert {"crash_reaction_v1.joblib", "crash_reaction_v1.json", "groups_test.csv"} <= files
    assert [int(v.version) for v in versions(uri)] == [1]


def test_logging_twice_does_not_duplicate(final_folder, uri, tmp_path):
    first = log_exported_model("final", final_folder, uri, tmp_path / "sin_grupos.csv")
    second = log_exported_model("final", final_folder, uri, tmp_path / "sin_grupos.csv")
    client = MlflowClient(uri)
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENTS["final"])
    assert first == second
    assert len(client.search_runs([experiment.experiment_id])) == 1
    assert len(versions(uri)) == 1


def test_keeps_the_real_training_time(exported, uri, tmp_path):
    meta = json.loads((exported / "crash_reaction_v1.json").read_text(encoding="utf-8"))
    run_id = log_exported_model("prototipo", exported, uri, tmp_path / "sin_grupos.csv")
    expected = int(datetime.fromisoformat(meta["trained_at"]).timestamp() * 1000)
    assert MlflowClient(uri).get_run(run_id).info.start_time == expected


def test_training_does_not_fail_if_mlflow_fails(monkeypatch, capsys):
    """Si MLflow falla, el entrenamiento sigue y avisa cómo registrarlo después."""
    def broken(kind):
        raise ConnectionError("servidor caído")
    monkeypatch.setattr(mlflow_tracking, "log_exported_model", broken)
    train.register_in_mlflow("final")
    output = capsys.readouterr().out
    assert "servidor caído" in output
    assert "uv run python -m bolsalab.modeling.mlflow_tracking final" in output


def test_files_go_next_to_the_database_in_use(exported, uri, tmp_path):
    """Con una base local, los archivos van a mlruns/ junto a esa base, no al proyecto."""
    run_id = log_exported_model("prototipo", exported, uri, tmp_path / "sin_grupos.csv")
    artifact_uri = MlflowClient(uri).get_run(run_id).info.artifact_uri
    assert artifact_uri.startswith((tmp_path / "mlruns").as_uri())


def test_failed_registration_leaves_no_half_run_and_retry_works(final_folder, uri, tmp_path, monkeypatch):
    """Si el registro de la versión falla, la corrida se borra y el reintento queda completo."""
    import mlflow

    def broken(*args, **kwargs):
        raise ConnectionError("registro caído")
    with monkeypatch.context() as patch:
        patch.setattr(mlflow, "register_model", broken)
        with pytest.raises(ConnectionError):
            log_exported_model("final", final_folder, uri, tmp_path / "sin_grupos.csv")
    client = MlflowClient(uri)
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENTS["final"])
    assert client.search_runs([experiment.experiment_id]) == []
    log_exported_model("final", final_folder, uri, tmp_path / "sin_grupos.csv")
    assert len(client.search_runs([experiment.experiment_id])) == 1
    assert [int(v.version) for v in versions(uri)] == [1]
