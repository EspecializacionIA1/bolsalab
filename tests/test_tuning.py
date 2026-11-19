"""Pruebas de los pasos 9 y 10 del ajuste por familias.

Usan datos inventados, salvo la última, que revisa el tipo de venta con los
datos reales de Japón cuando están en el computador.
"""

import numpy as np
import pandas as pd
import pytest
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier

from bolsalab.dataset import INVESTORS_FILE
from bolsalab.modeling.early_stopping import EarlyStoppingBooster
from bolsalab.modeling.train import TRAINING_FILE, evaluate_model, split_data
from bolsalab.modeling.tuning import (HELD, SOLD_ALL, SOLD_PART, ThreeClassModel,
                                      average_of_models, load_sale_type, trees_used,
                                      xgboost_with_optuna, xgboost_with_randomness)


@pytest.fixture(scope="module")
def data():
    """2.000 personas inventadas: una variable informa y otra es ruido; vende el ~20 %."""
    rng = np.random.default_rng(0)
    X = pd.DataFrame({"senal": rng.normal(size=2000), "ruido": rng.normal(size=2000)})
    y = pd.Series((rng.random(2000) < 1 / (1 + np.exp(1.5 - X["senal"]))).astype(int))
    return X, y


@pytest.fixture(scope="module")
def fitted_average(data):
    pipeline, _ = average_of_models()
    return pipeline.fit(*data)


def test_randomness_keeps_step_8_and_adds_three_ranges():
    """La aleatoriedad usa los mismos rangos del paso 8 y solo agrega tres."""
    _, step_8 = xgboost_with_optuna()
    _, ranges = xgboost_with_randomness()
    added = set(ranges) - set(step_8)
    assert {k: ranges[k] for k in step_8} == step_8
    assert added == {"model__estimator__subsample", "model__estimator__colsample_bytree",
                     "model__estimator__min_child_weight"}
    for name in ("model__estimator__subsample", "model__estimator__colsample_bytree"):
        _, low, high = ranges[name]
        assert 0 < low < high <= 1


def test_average_is_the_mean_of_the_three_models(data, fitted_average):
    """La probabilidad del promedio es la media simple de las tres, sin pesos."""
    X, _ = data
    members = fitted_average.named_steps["model"].named_estimators_
    mean = np.mean([m.predict_proba(X) for m in members.values()], axis=0)
    np.testing.assert_allclose(fitted_average.predict_proba(X), mean)


def test_average_reports_trees_of_each_booster(fitted_average):
    """En el promedio se guardan los árboles de XGBoost y CatBoost; la logística no tiene."""
    trees = trees_used(fitted_average)
    assert set(trees) == {"xgboost", "catboost"}
    assert all(n >= 1 for n in trees.values())


# --- Paso 10: etiqueta de tres clases ---

@pytest.fixture(scope="module")
def three_classes(data):
    """Los mismos datos con el tipo de venta: entre quienes venden, uno de cada cuatro vende todo."""
    X, y = data
    rng = np.random.default_rng(1)
    kind = np.where(y == 1, np.where(rng.random(len(y)) < 0.25, SOLD_ALL, SOLD_PART), HELD)
    return X, y, kind


def test_three_classes_returns_the_sum_of_both_sales(three_classes):
    """La probabilidad de vender es la suma de vender parte y vender todo."""
    X, y, kind = three_classes
    model = ThreeClassModel(XGBClassifier(n_estimators=20)).fit(X, y, sale_type=kind)
    p = model.estimator_.predict_proba(X)
    np.testing.assert_allclose(model.predict_proba(X)[:, 1], p[:, SOLD_PART] + p[:, SOLD_ALL],
                               rtol=1e-6)
    np.testing.assert_allclose(model.predict_proba(X).sum(axis=1), 1, rtol=1e-6)


def test_three_classes_rejects_a_sale_type_out_of_order(three_classes):
    """Si el tipo de venta no coincide con `sold`, no entrena."""
    X, y, kind = three_classes
    with pytest.raises(ValueError):
        ThreeClassModel(XGBClassifier(n_estimators=5)).fit(X, y, sale_type=kind[::-1])


def test_sale_type_reaches_each_fold_of_the_nested_validation(three_classes):
    """evaluate_model reparte el tipo de venta en cada partición sin desordenarlo."""
    X, y, kind = three_classes
    pipeline = Pipeline([("model", ThreeClassModel(XGBClassifier(n_estimators=20)))])
    metrics = evaluate_model(pipeline, {"model__estimator__max_depth": [2]}, X, y,
                             overfit_gap=True, fit_params={"model__sale_type": kind})
    assert 0.5 < metrics["auroc"] <= 1


@pytest.mark.skipif(not (INVESTORS_FILE.exists() and TRAINING_FILE.exists()),
                    reason="faltan los datos de Japón en este computador")
def test_sale_type_matches_sold_in_the_real_training_set():
    """Con los datos reales, quien vendió parte o todo es exactamente quien tiene sold = 1."""
    _, _, y_train, _ = split_data(pd.read_parquet(TRAINING_FILE))
    kind = load_sale_type(y_train.index)
    np.testing.assert_array_equal(kind != HELD, y_train.to_numpy() == 1)


def test_three_classes_counts_one_tree_per_class_and_round(three_classes):
    """Con tres clases, XGBoost hace tres árboles por ronda y así se cuentan."""
    X, y, kind = three_classes
    booster = EarlyStoppingBooster(XGBClassifier(n_estimators=200, learning_rate=0.3), patience=10)
    pipeline = Pipeline([("model", ThreeClassModel(booster))]).fit(X, y, model__sale_type=kind)
    rounds = pipeline.named_steps["model"].estimator_.n_trees_
    assert trees_used(pipeline) == rounds * 3


def test_fit_params_are_rejected_with_optuna(three_classes):
    """Optuna no recibe el tipo de venta: mejor fallar al empezar que al final."""
    X, y, kind = three_classes
    pipeline = Pipeline([("model", ThreeClassModel(XGBClassifier(n_estimators=5)))])
    with pytest.raises(ValueError):
        evaluate_model(pipeline, {"model__estimator__max_depth": ("int", 2, 3)}, X, y,
                       n_trials=2, fit_params={"model__sale_type": kind})
