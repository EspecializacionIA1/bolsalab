"""Pruebas del paso que cambia las variables en experiments.py."""

import numpy as np
import pandas as pd
import pytest

from bolsalab.features import FEATURES
from bolsalab.modeling.experiments import FEATURE_SETS
from bolsalab.modeling.transformers import FeatureEngineer
from bolsalab.modeling.tuning import STEPS


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


@pytest.fixture
def people():
    """Cuatro personas inventadas; el promedio de aciertos es 1,75."""
    return pd.DataFrame({
        "knows_interest":        [1, 1, 0, 0],
        "knows_inflation":       [1, 1, 0, 1],
        "knows_diversification": [1, 1, 0, 0],
        "knowledge_confidence":  [5, 2, 4, 5],
        "overconfidence":        [1, 0, 1, 1],
        "male":                  [1, 0, 1, 0],
        "income_bracket":        [1, 2, 2, 9],
        "assets_bracket":        [2, 5, 1, 1],
    })


def test_correct_answers_adds_the_three_questions(people):
    result = FeatureEngineer(add_correct_answers=True).fit_transform(people)
    assert list(result["correct_answers"]) == [3, 3, 0, 1]


def test_unjustified_confidence_follows_the_article(people):
    """Confianza 5 con los 3 aciertos no cuenta; la columna vieja se quita."""
    result = FeatureEngineer(unjustified_confidence=True).fit_transform(people)
    assert list(result["unjustified_confidence"]) == [0, 0, 1, 1]
    assert "overconfidence" not in result.columns


def test_unjustified_confidence_uses_the_training_average(people):
    """El promedio de aciertos se aprende al entrenar y se reutiliza al medir."""
    step = FeatureEngineer(unjustified_confidence=True).fit(people)
    one_person = people.iloc[[3]]
    assert step.mean_correct_ == 1.75
    assert list(step.transform(one_person)["unjustified_confidence"]) == [1]


def test_man_with_few_correct(people):
    """Solo el hombre con 0 o 1 aciertos; la mujer con 1 acierto no."""
    result = FeatureEngineer(man_with_few_correct=True).fit_transform(people)
    assert list(result["man_with_few_correct"]) == [0, 0, 1, 0]


def test_low_financial_cushion_needs_both(people):
    """Ingreso bajo con activos medios, o al revés, no cuenta."""
    result = FeatureEngineer(low_financial_cushion=True).fit_transform(people)
    assert list(result["low_financial_cushion"]) == [1, 0, 1, 0]


def test_categorical_keeps_the_training_groups(people):
    """Los grupos se aprenden al entrenar: una persona sola conserva los mismos."""
    step = FeatureEngineer(categorical=["income_bracket"]).fit(people)
    result = step.transform(people.iloc[[0]])
    assert list(result["income_bracket"].cat.categories) == [1, 2, 9]


def test_step_5_changes_only_the_columns():
    """Las pruebas de variables usan la rejilla del paso 2 y columnas que existen."""
    _, pruning_grid = STEPS[2]["xgboost|poda"][0]()
    table = pd.DataFrame(0, index=range(4), columns=FEATURES)
    for build, _ in STEPS[5].values():
        pipeline, grid = build()
        assert grid == pruning_grid
        pipeline.named_steps["variables"].fit_transform(table)


def test_xgboost_trains_with_brackets_as_groups():
    """El XGBoost con parada temprana acepta los tramos como grupos."""
    rng = np.random.default_rng(0)
    table = pd.DataFrame(rng.integers(1, 6, size=(400, len(FEATURES))), columns=FEATURES)
    target = pd.Series((table["income_bracket"] == 1).astype(int))
    pipeline, _ = STEPS[5]["variables|tramos_como_grupos"][0]()
    pipeline.fit(table, target)
    assert pipeline.predict_proba(table).shape == (400, 2)


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
