"""Pruebas del paso que cambia las variables en experiments.py."""

import numpy as np
import pandas as pd
import pytest

from bolsalab.modeling.experiments import FEATURE_SETS
from bolsalab.modeling.transformers import FeatureEngineer
from bolsalab.features import FEATURES


@pytest.fixture
def table():
    return pd.DataFrame({"age": [30, 50], "age_squared": [900, 2500], "income_bracket": [1, 3]})


def test_without_changes_returns_same_table(table):
    """Sin opciones, la tabla sale igual."""
    pd.testing.assert_frame_equal(FeatureEngineer().fit_transform(table), table)


def test_drop_removes_column(table):
    """drop quita la columna pedida y deja las demás."""
    result = FeatureEngineer(drop=["age_squared"]).fit_transform(table)
    assert list(result.columns) == ["age", "income_bracket"]


def test_log_uses_log1p(table):
    """log cambia el valor por log(1 + valor)."""
    result = FeatureEngineer(log=["income_bracket"]).fit_transform(table)
    assert np.allclose(result["income_bracket"], np.log1p([1, 3]))


def test_interaction_adds_product(table):
    """interactions agrega la multiplicación de las dos columnas."""
    result = FeatureEngineer(interactions=[("age", "income_bracket")]).fit_transform(table)
    assert list(result["age_x_income_bracket"]) == [30, 150]


def test_unknown_column_fails(table):
    """Una columna que no existe detiene el experimento en vez de ignorarse."""
    with pytest.raises(ValueError, match="no existen"):
        FeatureEngineer(drop=["ingreso"]).fit(table)


def test_feature_sets_use_real_columns():
    """Toda variante de experiments.py usa columnas de las 17 variables."""
    for options in FEATURE_SETS.values():
        FeatureEngineer(**options).fit(pd.DataFrame(columns=FEATURES))


def test_evaluate_model_records_chosen_params():
    """evaluate_model guarda los hiperparámetros que eligió cada una de las 5 particiones."""
    import json

    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    from bolsalab.modeling.train import evaluate_model

    rng = np.random.default_rng(0)
    X = pd.DataFrame({"a": rng.normal(size=200), "b": rng.normal(size=200)})
    y = pd.Series((X["a"] + rng.normal(size=200) > 0).astype(int))
    pipeline = Pipeline([("model", LogisticRegression())])
    metrics = evaluate_model(pipeline, {"model__C": [0.1, 1]}, X, y)
    chosen = json.loads(metrics["best_params"])
    assert len(chosen) == 5
    assert all(params["model__C"] in (0.1, 1) for params in chosen)
