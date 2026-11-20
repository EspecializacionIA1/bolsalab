"""Pruebas del registro en MLflow del modelo exportado.

Usan un modelo pequeño con datos inventados, una carpeta temporal y un MLflow
temporal. No tocan models/, el mlflow.db del proyecto ni el 20 % de prueba.
"""

import json
import shutil
from datetime import datetime

import mlflow
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
FAKE_GROUPS = [{"grupo": "Sexo", "valor": "Hombres", "auroc": 0.62}]


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


def copy_with(folder, tmp_path, name, **changes):
    """Copia del modelo exportado con cambios en su .json."""
    copy = tmp_path / name
    shutil.copytree(folder, copy)
    path = copy / "crash_reaction_v1.json"
    meta = {**json.loads(path.read_text(encoding="utf-8")), **changes}
    path.write_text(json.dumps({k: v for k, v in meta.items() if v is not ...}), encoding="utf-8")
    return copy


@pytest.fixture
def final_folder(exported, tmp_path):
    """El modelo como lo deja --final: con resultados de prueba y sus grupos."""
    return copy_with(exported, tmp_path, "final", test=FAKE_TEST, test_groups=FAKE_GROUPS)


@pytest.fixture
def uri(tmp_path):
    return f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}"


def versions(uri):
    return MlflowClient(uri).search_model_versions(f"name='{MLFLOW_REGISTERED_MODEL}'")


def final_runs(uri):
    client = MlflowClient(uri)
    experiment = client.get_experiment_by_name(MLFLOW_EXPERIMENTS["final"])
    return client.search_runs([experiment.experiment_id])


def test_prototype_logs_a_run_without_a_model_version(exported, uri):
    """Sin resultados de prueba, la corrida es un prototipo y no crea versión."""
    run = MlflowClient(uri).get_run(log_exported_model(exported, uri))
    assert run.data.tags["tipo"] == "prototipo"
    assert run.data.params["configuracion"] == "xgboost|poda"
    assert run.data.params["gamma"] == "0.5"
    assert "cv_auroc" in run.data.metrics
    assert not any(name.startswith("test_") for name in run.data.metrics)
    assert versions(uri) == []


def test_final_logs_test_metrics_groups_and_version_one(final_folder, uri):
    """Con resultados de prueba, la corrida es final y crea la versión 1."""
    run_id = log_exported_model(final_folder, uri)
    client = MlflowClient(uri)
    run = client.get_run(run_id)
    assert run.data.tags["tipo"] == "final"
    assert run.data.metrics["test_auroc"] == pytest.approx(0.66)
    assert run.data.metrics["test_auroc_ci95_bajo"] == pytest.approx(0.65)
    files = {artifact.path for artifact in client.list_artifacts(run_id)}
    assert {"crash_reaction_v1.joblib", "crash_reaction_v1.json", "groups_test.json"} <= files
    assert [int(v.version) for v in versions(uri)] == [1]


def test_registered_model_predicts_like_the_package(final_folder, uri):
    """El modelo del registro da las mismas probabilidades que el .joblib."""
    log_exported_model(final_folder, uri)
    mlflow.set_tracking_uri(uri)
    registered = mlflow.sklearn.load_model(f"models:/{MLFLOW_REGISTERED_MODEL}/1")
    package = mlflow_tracking.joblib.load(final_folder / "crash_reaction_v1.joblib")
    X = pd.DataFrame(np.zeros((3, len(package["features"]))), columns=package["features"])
    np.testing.assert_allclose(registered.predict_proba(X), package["model"].predict_proba(X))


def test_logging_twice_does_not_duplicate(final_folder, uri):
    first = log_exported_model(final_folder, uri)
    second = log_exported_model(final_folder, uri)
    assert first == second
    assert len(final_runs(uri)) == 1
    assert len(versions(uri)) == 1


def test_keeps_the_real_training_time(exported, uri):
    meta = json.loads((exported / "crash_reaction_v1.json").read_text(encoding="utf-8"))
    run_id = log_exported_model(exported, uri)
    expected = int(datetime.fromisoformat(meta["trained_at"]).timestamp() * 1000)
    assert MlflowClient(uri).get_run(run_id).info.start_time == expected


def test_old_model_without_training_time_gives_a_clear_message(exported, uri, tmp_path):
    old = copy_with(exported, tmp_path, "viejo", trained_at=...)
    with pytest.raises(ValueError, match="--prototype"):
        log_exported_model(old, uri)


def test_files_go_next_to_the_database_in_use(exported, uri, tmp_path):
    """Con una base local, los archivos van a mlruns/ junto a esa base, no al proyecto."""
    artifact_uri = MlflowClient(uri).get_run(log_exported_model(exported, uri)).info.artifact_uri
    assert artifact_uri.startswith((tmp_path / "mlruns").as_uri())


def test_failed_registration_leaves_no_half_run_and_retry_works(final_folder, uri, monkeypatch):
    """Si el registro de la versión falla, la corrida se borra y el reintento queda completo."""
    def broken(*args, **kwargs):
        raise ConnectionError("registro caído")
    with monkeypatch.context() as patch:
        patch.setattr(mlflow, "register_model", broken)
        with pytest.raises(ConnectionError):
            log_exported_model(final_folder, uri)
    assert final_runs(uri) == []
    log_exported_model(final_folder, uri)
    assert len(final_runs(uri)) == 1
    assert [int(v.version) for v in versions(uri)] == [1]


def test_training_does_not_fail_if_mlflow_fails(monkeypatch, capsys):
    """Si MLflow falla, el entrenamiento sigue y avisa cómo registrarlo después."""
    def broken():
        raise ConnectionError("servidor caído")
    monkeypatch.setattr(mlflow_tracking, "log_exported_model", broken)
    train.register_in_mlflow()
    output = capsys.readouterr().out
    assert "servidor caído" in output
    assert "uv run python -m bolsalab.modeling.mlflow_tracking" in output


def test_leaves_the_global_mlflow_address_as_it_was(final_folder, uri, tmp_path):
    before = f"sqlite:///{(tmp_path / 'otra.db').as_posix()}"
    mlflow.set_tracking_uri(before)
    log_exported_model(final_folder, uri)
    assert mlflow.get_tracking_uri() == before


def test_registered_model_gives_probabilities_to_any_reader(final_folder, uri):
    """Cargado de forma genérica (como lo haría una API), devuelve probabilidades."""
    log_exported_model(final_folder, uri)
    mlflow.set_tracking_uri(uri)
    generic = mlflow.pyfunc.load_model(f"models:/{MLFLOW_REGISTERED_MODEL}/1")
    package = mlflow_tracking.joblib.load(final_folder / "crash_reaction_v1.joblib")
    X = pd.DataFrame(np.zeros((3, len(package["features"]))), columns=package["features"])
    np.testing.assert_allclose(generic.predict(X), package["model"].predict_proba(X))
