"""Pruebas de la tabla de la NFCS 2018. Las cifras esperadas están en docs/nfcs.md."""

import pytest

from bolsalab.config import NFCS_INVESTOR_ZIP, NFCS_STATE_ZIP
from bolsalab.nfcs import build_target, load_nfcs_2018, select_respondents

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


def test_respondents_exclude_dont_know(respondents):
    """Quedan 1.942: se excluyen 43 'no sabe' y 18 'prefiere no decir'."""
    assert len(respondents) == 1942


def test_sold_counts(respondents):
    """Vendieron 87; compraron 396 y no hicieron nada 1.459, y esos cuentan como 0."""
    sold = build_target(respondents)
    assert sold.sum() == 87
    assert (sold == 0).sum() == 396 + 1459
