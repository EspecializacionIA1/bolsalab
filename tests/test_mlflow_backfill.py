"""Pruebas de la carga de pruebas en MLflow, con CSV inventados y un MLflow temporal.

No tocan el mlflow.db del proyecto.
"""

from datetime import datetime

import pandas as pd
import pytest
from mlflow.tracking import MlflowClient

from bolsalab.config import MLFLOW_EXPERIMENTS
from bolsalab.modeling.mlflow_backfill import backfill, how_to_see


@pytest.fixture
def files(tmp_path):
    benchmark = tmp_path / "benchmark.csv"
    pd.DataFrame({"model": ["trivial", "xgboost"], "auroc": [0.5, 0.66], "auroc_sd": [0.0, 0.003]}
                 ).to_csv(benchmark, index=False)
    tuning = tmp_path / "tuning.csv"
    pd.DataFrame({
        "step": [1, 2, 2],
        "experiment": ["xgboost|parada_temprana", "xgboost|poda", "xgboost|poda"],
        "reason": ["primera", "vieja", "nueva"],
        "grid": ["{}", "{}", "{}"],
        "auroc": [0.6594, 0.6000, 0.6595],
        "best_params": ["[]", "[]", "[]"],
        "fold_detail": ["[1]", "[2]", "[3]"],
        "run_at": ["2026-11-05T20:55:43", "2026-11-05T21:00:00", "2026-11-05T21:04:41"],
    }).to_csv(tuning, index=False)
    return f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}", benchmark, tuning


def runs(uri, key):
    client = MlflowClient(uri)
    exp = client.get_experiment_by_name(MLFLOW_EXPERIMENTS[key])
    return {r.info.run_name: r for r in client.search_runs([exp.experiment_id])}


def test_loads_every_test_once_and_keeps_the_last_rerun(files):
    """Una corrida por prueba; si una prueba se repitió, vale la última."""
    uri, benchmark, tuning = files
    assert backfill(uri, benchmark, tuning) == {"comparacion": 2, "ajuste": 2}
    pruning = runs(uri, "ajuste")["xgboost|poda"]
    assert pruning.data.metrics["auroc"] == pytest.approx(0.6595)
    assert pruning.data.tags["razon"] == "nueva"
    assert pruning.data.tags["reentrenado"] == "no"
    assert pruning.data.params["step"] == "2"


def test_running_twice_does_not_duplicate(files):
    uri, benchmark, tuning = files
    backfill(uri, benchmark, tuning)
    assert backfill(uri, benchmark, tuning) == {"comparacion": 0, "ajuste": 0}
    assert len(runs(uri, "comparacion")) == 2


def test_keeps_the_original_date_of_each_test(files):
    uri, benchmark, tuning = files
    backfill(uri, benchmark, tuning)
    early = runs(uri, "ajuste")["xgboost|parada_temprana"]
    expected = int(datetime.fromisoformat("2026-11-05T20:55:43").timestamp() * 1000)
    assert early.info.start_time == expected


def test_files_go_next_to_the_database_in_use(files, tmp_path):
    uri, benchmark, tuning = files
    backfill(uri, benchmark, tuning)
    experiment = MlflowClient(uri).get_experiment_by_name(MLFLOW_EXPERIMENTS["ajuste"])
    assert experiment.artifact_location.startswith((tmp_path / "mlruns").as_uri())


def test_a_test_run_again_later_replaces_the_old_run(files):
    """Si una prueba se vuelve a correr (otra fecha), MLflow queda con el resultado nuevo."""
    uri, benchmark, tuning = files
    backfill(uri, benchmark, tuning)
    rows = pd.read_csv(tuning)
    rerun = rows.iloc[[0]].assign(auroc=0.7, run_at="2026-11-20T10:00:00")
    pd.concat([rows, rerun]).to_csv(tuning, index=False)
    assert backfill(uri, benchmark, tuning) == {"comparacion": 0, "ajuste": 1}
    early = runs(uri, "ajuste")["xgboost|parada_temprana"]
    assert early.data.metrics["auroc"] == pytest.approx(0.7)
    assert len(runs(uri, "ajuste")) == 2


def test_a_row_without_date_does_not_break(files):
    uri, benchmark, tuning = files
    rows = pd.read_csv(tuning)
    rows.loc[0, "run_at"] = None
    rows.to_csv(tuning, index=False)
    assert backfill(uri, benchmark, tuning) == {"comparacion": 2, "ajuste": 2}


def test_source_is_relative_to_the_project():
    from bolsalab.config import PROJ_ROOT
    from bolsalab.modeling.mlflow_backfill import source_name
    assert source_name(PROJ_ROOT / "reports" / "tuning.csv") == "reports/tuning.csv"


def test_short_relative_sqlite_address_works(tmp_path, monkeypatch):
    """La forma corta de la documentación de MLflow (sqlite:///mlflow.db) no rompe."""
    from bolsalab.modeling.mlflow_backfill import artifact_location
    monkeypatch.chdir(tmp_path)
    assert artifact_location("sqlite:///mlflow.db") == (tmp_path / "mlruns").as_uri()
    assert artifact_location("http://servidor:5000") is None


def test_how_to_see_depends_on_where_runs_are():
    """Con base local se levanta la interfaz; con servidor se abre la dirección."""
    assert how_to_see("sqlite:///C:/x/mlflow.db").startswith("uv run mlflow ui")
    assert how_to_see("https://mlflow.ejemplo.com") == "abre https://mlflow.ejemplo.com en el navegador"
