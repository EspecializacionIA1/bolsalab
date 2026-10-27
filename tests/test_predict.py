"""Pruebas de la predicción para una persona (bolsalab/modeling/predict.py) y de la app."""

import pytest

from bolsalab.config import PROJ_ROOT
from bolsalab.modeling.predict import (
    ARTIFACT,
    CrashReactionModel,
    build_features,
    check_answers,
    overconfident,
)

REFERENCE = {
    "features": ["knows_interest", "knows_inflation", "knows_diversification",
                 "knowledge_confidence", "overconfidence", "age", "age_squared", "male",
                 "university", "married", "has_children", "urban", "employed",
                 "risk_aversion", "short_term_view", "income_bracket", "assets_bracket"],
    "income_level_to_bracket": {"1": 3, "2": 4, "3": 5, "4": 6, "5": 8},
    "assets_level_to_bracket": {"1": 1, "2": 3, "3": 5, "4": 7, "5": 9},
    "not_asked": {"risk_aversion": 0.5, "short_term_view": 2.0},
}


@pytest.fixture
def answers():
    return {"age": 27, "male": False, "university": True, "married": False,
            "has_children": False, "urban": True, "employed": True,
            "income_level": 3, "assets_level": 1,
            "interest": "more", "inflation": "dont_know", "diversification": "false",
            "knowledge_confidence": 4}


def test_overconfidence_rule():
    """Marcó 5, o marcó 4 y acertó 2 o menos: la regla del archivo japonés."""
    assert overconfident(5, 3)
    assert overconfident(4, 2)
    assert not overconfident(4, 3)
    assert not overconfident(3, 0)


def test_features_in_model_order(answers):
    """Salen las 17 variables, en el orden con que se entrenó el modelo."""
    assert list(build_features(answers, REFERENCE).columns) == REFERENCE["features"]


def test_knowledge_and_derived_values(answers):
    """'No sé' cuenta como error; edad² y exceso de confianza se calculan, no se preguntan."""
    row = build_features(answers, REFERENCE).iloc[0]
    knowledge = ["knows_interest", "knows_inflation", "knows_diversification"]
    assert row[knowledge].tolist() == [1, 0, 1]
    assert row["age_squared"] == 27 ** 2
    assert row["overconfidence"] == 1


def test_levels_and_not_asked(answers):
    """Los niveles van al tramo japonés guardado; las preguntas que no se hacen, al valor común."""
    row = build_features(answers, REFERENCE).iloc[0]
    assert row["income_bracket"] == 5
    assert row["assets_bracket"] == 1
    assert row["risk_aversion"] == 0.5
    assert row["short_term_view"] == 2.0


def test_wrong_answers_stop_prediction(answers):
    """Una respuesta que falta o que no existe detiene la predicción."""
    with pytest.raises(ValueError, match="Faltan"):
        check_answers({k: v for k, v in answers.items() if k != "age"})
    with pytest.raises(ValueError, match="interest"):
        check_answers({**answers, "interest": "102"})
    with pytest.raises(ValueError, match="income_level"):
        check_answers({**answers, "income_level": 6})


needs_model = pytest.mark.skipif(not ARTIFACT.exists(), reason="Falta models/crash_reaction_v1")


@needs_model
def test_prediction_result(answers):
    """Devuelve una de las tres categorías y los factores sin las preguntas que no se hacen."""
    result = CrashReactionModel().predict(answers)
    assert result["category"] in {"less_likely", "similar", "more_likely"}
    features = {f["feature"] for f in result["top_factors"]}
    assert len(features) == 4
    assert not features & {"risk_aversion", "short_term_view", "age_squared"}
    assert result["failed_questions"] == ["inflation"]


@needs_model
def test_category_follows_cutoffs():
    """Bajo el primer corte es 'menos'; desde el segundo, 'más'."""
    model = CrashReactionModel()
    low, high = model.metadata["cutoffs"]
    assert model.category(low - 0.01) == "less_likely"
    assert model.category(low) == "similar"
    assert model.category(high) == "more_likely"


@needs_model
def test_app_shows_result():
    """La app responde el cuestionario completo y muestra el resultado sin errores."""
    testing = pytest.importorskip("streamlit.testing.v1")
    app = testing.AppTest.from_file(str(PROJ_ROOT / "app" / "app.py"), default_timeout=60).run()
    for radio, choice in zip(app.radio[-4:], ["Más de $102", "Menos que hoy", "Falso",
                                              "Algo de acuerdo"], strict=True):
        radio.set_value(choice)
    app.button[0].click().run()
    assert not app.exception
    assert any("tercio" in m.value for m in app.markdown)
