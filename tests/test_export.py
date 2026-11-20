"""Pruebas del paquete que exporta train.py, con datos inventados y una carpeta temporal.

No usan el modelo de models/ ni el 20 % de prueba.
"""

import hashlib
import json
from datetime import datetime

import joblib
import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from bolsalab.modeling import train
from bolsalab.modeling.early_stopping import EarlyStoppingBooster
from bolsalab.modeling.predict import CrashReactionModel


@pytest.fixture(scope="module")
def data():
    """800 personas inventadas con las columnas que necesita la metadata de la app."""
    rng = np.random.default_rng(0)
    n = 800
    age = rng.integers(18, 80, n)
    X = pd.DataFrame({"signal": rng.normal(size=n), "age": age, "age_squared": age ** 2,
                      "income_bracket": rng.integers(1, 13, n), "assets_bracket": rng.integers(1, 11, n),
                      "risk_aversion": rng.integers(0, 11, n) / 10, "short_term_view": rng.integers(1, 6, n)})
    y = pd.Series((rng.random(n) < 1 / (1 + np.exp(1.5 - X["signal"]))).astype(int))
    return X, y


@pytest.fixture(scope="module")
def exported(data, tmp_path_factory):
    """Entrena un modelo pequeño con parada temprana y lo exporta a una carpeta temporal."""
    X, y = data
    folder = tmp_path_factory.mktemp("models")
    table = folder / "tabla.parquet"
    X.assign(sold=y).to_parquet(table)
    model = Pipeline([("model", EarlyStoppingBooster(XGBClassifier(n_estimators=200), patience=10))]).fit(X, y)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(train, "MODELS_DIR", folder)
        mp.setattr(train, "TRAINING_FILE", table)
        train.export_model(model, {"winner": "prueba", "params": {}, "test": None}, X, y, y.iloc[:200])
    return folder, table, model


def test_package_has_model_explainer_features_and_classes(exported, data):
    folder, _, model = exported
    X, _ = data
    artifact = joblib.load(folder / "crash_reaction_v1.joblib")
    assert set(artifact) == {"model", "explainer", "features", "classes"}
    assert artifact["features"] == list(X.columns)
    assert artifact["classes"] == [0, 1]
    np.testing.assert_allclose(artifact["model"].predict_proba(X), model.predict_proba(X))


def test_saved_explainer_matches_the_prediction(exported, data):
    """SHAP explica los mismos árboles que usa la predicción (los de la parada temprana)."""
    folder, _, _ = exported
    X, _ = data
    artifact = joblib.load(folder / "crash_reaction_v1.joblib")
    p = artifact["model"].predict_proba(X[:50])[:, 1]
    explanation = artifact["explainer"](X[:50])
    np.testing.assert_allclose(explanation.values.sum(axis=1) + explanation.base_values,
                               np.log(p / (1 - p)), atol=1e-4)


def test_metadata_records_data_split_versions_and_code(exported, data):
    folder, table, _ = exported
    _, y = data
    metadata = json.loads((folder / "crash_reaction_v1.json").read_text(encoding="utf-8"))
    assert metadata["dataset_sha256"] == hashlib.sha256(table.read_bytes()).hexdigest()
    assert metadata["split"]["train_rows"] == len(y)
    assert metadata["split"]["test_rows"] == 200
    assert set(metadata["versions"]) == {"python", "sklearn", "xgboost", "shap", "numpy", "pandas"}
    assert set(metadata["git"]) == {"commit", "uncommitted_changes"}
    assert metadata["cv_estimate"]["auroc"] == pytest.approx(0.6595, abs=0.001)
    trained_at = datetime.fromisoformat(metadata["trained_at"])
    assert trained_at.date().isoformat() == metadata["trained_on"]


def test_predict_loads_the_package(exported, data):
    """predict.py usa el explicador guardado y no muestra las preguntas que la app no hace."""
    folder, _, _ = exported
    X, _ = data
    model = CrashReactionModel(folder / "crash_reaction_v1.joblib")
    contributions = model.explain(X.iloc[[0]])
    assert "age_squared" not in contributions
    assert not {"risk_aversion", "short_term_view"} & set(contributions.index)


def test_top_ten_percent_is_who_sold_among_the_highest_risk():
    """Con 100 personas, el 10 % de mayor riesgo son las 10 de probabilidad más alta."""
    class Fixed:
        def predict_proba(self, X):
            p = np.linspace(0.01, 0.99, 100)
            return np.column_stack([1 - p, p])

    # 20 ventas entre las 90 de menor riesgo y 3 entre las 10 de mayor riesgo
    y = pd.Series([1, 0, 0, 0] * 5 + [0] * 70 + [1, 1, 1, 0, 0, 0, 0, 0, 0, 0])
    metrics = train.evaluate_on_test(Fixed(), pd.DataFrame(index=range(100)), y)
    assert metrics["sold_rate_top10"] == pytest.approx(0.3)
    assert metrics["sold_rate"] == pytest.approx(0.08)
