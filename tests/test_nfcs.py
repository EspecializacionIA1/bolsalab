"""Pruebas de la tabla de la NFCS 2018. Las cifras esperadas están en docs/nfcs.md."""

import pytest

from bolsalab.config import NFCS_INVESTOR_ZIP, NFCS_STATE_ZIP
from bolsalab.nfcs import (
    DEMOGRAPHICS,
    build_confidence,
    build_demographics,
    build_knowledge,
    build_risk_aversion,
    build_target,
    load_nfcs_2018,
    select_respondents,
)

pytestmark = pytest.mark.skipif(
    not (NFCS_INVESTOR_ZIP.exists() and NFCS_STATE_ZIP.exists()),
    reason="Faltan los archivos de la NFCS en data/external (no se versionan ni se comparten)",
)


@pytest.fixture(scope="module")
def survey():
    """Las dos partes unidas, cargadas una sola vez."""
    return load_nfcs_2018()


@pytest.fixture(scope="module")
def respondents(survey):
    return select_respondents(survey)


def test_every_investor_finds_state_record(survey):
    """Las 2.003 personas de inversionistas encuentran su fila en State-by-State."""
    assert len(survey) == 2003
    assert survey["STATEQ"].notna().all()


def test_repeated_codes_are_kept_apart(survey):
    """A3 existe en las dos partes con preguntas distintas y no se mezclan."""
    assert {"A3_inv", "A3_state"} <= set(survey.columns)


def test_everyone_has_non_retirement_investments(survey):
    """La encuesta solo dejó seguir a quien tenía inversiones fuera de retiro."""
    assert survey["A3_inv"].eq(1).all()


def test_respondents(respondents):
    """Quedan 1.918: 1.942 dijeron qué hicieron; salen 14 sin calificar su conocimiento y 10 sin calificar su riesgo."""
    assert len(respondents) == 1918


def test_sold_counts(respondents):
    """Vendieron 85; compraron 389 y no hicieron nada 1.444, y esos cuentan como 0."""
    sold = build_target(respondents)
    assert sold.sum() == 85
    assert (sold == 0).sum() == 389 + 1444


@pytest.fixture(scope="module")
def demographics(respondents):
    return build_demographics(respondents)


def test_demographics_have_japan_names(demographics):
    """Las columnas se llaman igual que en la tabla de Japón."""
    assert list(demographics.columns) == DEMOGRAPHICS


def test_age_uses_range_midpoints(demographics):
    """La edad es el punto medio de cada rango; 70 para '65 o más'."""
    assert set(demographics["age"].unique()) <= {21, 29.5, 39.5, 49.5, 59.5, 70}
    assert (demographics["age_squared"] == demographics["age"] ** 2).all()


def test_demographic_counts(demographics):
    """Cuántas personas tienen 1 en cada variable de sí o no."""
    assert demographics["male"].sum() == 1098
    assert demographics["university"].sum() == 1090
    assert demographics["married"].sum() == 1224
    assert demographics["has_children"].sum() == 1351
    assert demographics["employed"].sum() == 985


def test_demographics_no_missing(demographics):
    """Nadie queda sin dato: la encuesta no dejaba saltar estas preguntas."""
    assert not demographics.isna().any().any()


def test_knowledge_counts(respondents):
    """Cuántos acertaron cada pregunta; 'no sabe' y 'prefiere no decir' cuentan como 0."""
    knowledge = build_knowledge(respondents)
    assert knowledge["knows_interest"].sum() == 1667
    assert knowledge["knows_inflation"].sum() == 1518
    assert knowledge["knows_diversification"].sum() == 1381
    assert set(knowledge.stack().unique()) <= {0, 1}


@pytest.fixture(scope="module")
def confidence(respondents):
    return build_confidence(respondents, build_knowledge(respondents))


def test_confidence_uses_japan_scale(confidence):
    """La confianza queda de 1 a 5, como en Japón."""
    assert confidence["knowledge_confidence"].value_counts().to_dict() == {
        4: 1298, 5: 442, 3: 144, 2: 29, 1: 5}


def test_overconfidence_follows_japan_rule(confidence):
    """Exceso de confianza: marcó 5, o marcó 4 y acertó 2 o menos. Son 922."""
    assert confidence["overconfidence"].sum() == 922


def test_risk_aversion_is_inverted(respondents):
    """Quien marca 1 en J2 (nada dispuesto) queda en 1; quien marca 10, en 0."""
    risk = build_risk_aversion(respondents)
    assert risk[respondents["J2"] == 1].eq(1).all()
    assert risk[respondents["J2"] == 10].eq(0).all()
    assert risk.between(0, 1).all()
