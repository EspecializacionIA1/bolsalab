"""Pruebas del envoltorio de parada temprana con datos inventados (no usa la encuesta)."""

import numpy as np
import pandas as pd
import pytest
from lightgbm import LGBMClassifier
from sklearn.model_selection import GridSearchCV, StratifiedKFold
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from bolsalab.modeling.early_stopping import EarlyStoppingBooster


@pytest.fixture(scope="module")
def data():
    """2.000 personas inventadas: una variable informa y otra es ruido; vende el ~20 %."""
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"senal": rng.normal(size=2000), "ruido": rng.normal(size=2000)})
    y = pd.Series((rng.random(2000) < 1 / (1 + np.exp(1.5 - X["senal"]))).astype(int))
    return X, y


@pytest.mark.parametrize("estimator", [
    XGBClassifier(n_estimators=1000, learning_rate=0.3),
    LGBMClassifier(n_estimators=1000, learning_rate=0.3, verbose=-1),
])
def test_stops_before_the_cap(data, estimator):
    """Con velocidad alta y una sola señal, para mucho antes de los 1.000 árboles."""
    model = EarlyStoppingBooster(estimator, patience=20).fit(*data)
    assert 1 <= model.n_trees_ < 1000


def test_xgboost_predicts_with_best_trees(data):
    """predict_proba usa solo los árboles hasta el mejor punto, no los 20 de espera."""
    X, y = data
    model = EarlyStoppingBooster(XGBClassifier(n_estimators=1000, learning_rate=0.3),
                                 patience=20).fit(X, y)
    best = model.estimator_.predict_proba(X, iteration_range=(0, model.n_trees_))
    np.testing.assert_allclose(model.predict_proba(X), best)


def test_works_inside_grid_search(data):
    """GridSearchCV puede mover los hiperparámetros del modelo envuelto y medir AUROC."""
    pipeline = Pipeline([("model", EarlyStoppingBooster(XGBClassifier(n_estimators=500)))])
    grid = {"model__estimator__max_depth": [2, 3]}
    search = GridSearchCV(pipeline, grid, cv=StratifiedKFold(3), scoring="roc_auc").fit(*data)
    assert search.best_score_ > 0.6


def test_rejects_other_models(data):
    """Solo admite XGBoost y LightGBM; CatBoost usa su propio eval_fraction."""
    from sklearn.linear_model import LogisticRegression
    with pytest.raises(TypeError):
        EarlyStoppingBooster(LogisticRegression()).fit(*data)
