"""Pruebas de la API (backend/app/main.py) con el modelo publicado en models/."""

import re

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app, limiter
from bolsalab.config import API_RATE_LIMIT
from bolsalab.modeling.predict import ACTIONABLE

PREDICT = "/api/v1/crash-reaction/predict"


@pytest.fixture
def client():
    # Cada prueba empieza con el contador de peticiones en cero.
    limiter.reset()
    with TestClient(app) as client:
        yield client


@pytest.fixture
def answers():
    return {"age": 27, "male": False, "university": True, "married": False,
            "has_children": False, "urban": True, "employed": True,
            "income_level": 3, "assets_level": 1, "knowledge_confidence": 4,
            "interest": "more", "inflation": "dont_know", "diversification": "false"}


def test_health(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "model_version": "crash_reaction_v1"}


def test_predict_returns_category_and_factors(client, answers):
    response = client.post(PREDICT, json=answers)
    assert response.status_code == 200
    body = response.json()
    assert body["category"] in {"less_likely", "similar", "more_likely"}
    assert body["top_factors"]
    assert body["failed_questions"] == ["inflation"]


def test_predict_never_returns_the_probability(client, answers):
    body = client.post(PREDICT, json=answers).json()
    assert "probability" not in body
    assert "base_rate" not in body


@pytest.mark.parametrize("change", [
    {"income_level": 9},
    {"interest": "mucho"},
    {"age": "veinte"},
    {"age": 15},
])
def test_invalid_answers_are_rejected(client, answers, change):
    assert client.post(PREDICT, json={**answers, **change}).status_code == 422


def test_missing_answer_is_rejected(client, answers):
    del answers["urban"]
    assert client.post(PREDICT, json=answers).status_code == 422


def test_too_many_requests_from_the_same_ip(client, answers):
    limit = int(API_RATE_LIMIT.split("/")[0])  # "30/minute" -> 30
    for _ in range(limit):
        assert client.post(PREDICT, json=answers).status_code == 200
    response = client.post(PREDICT, json=answers)
    assert response.status_code == 429
    assert "Demasiadas" in response.json()["detail"]


# --- Reglas de negocio: casos verificados con el modelo congelado crash_reaction_v1 ---

DONT_KNOW = {"interest": "dont_know", "inflation": "dont_know", "diversification": "dont_know"}
ALL_RIGHT = {"interest": "more", "inflation": "less", "diversification": "false"}
PROFILES = {
    "experto": {**ALL_RIGHT, "knowledge_confidence": 4},
    "sobreconfiado": {**DONT_KNOW, "knowledge_confidence": 5},
    "humilde": {**DONT_KNOW, "knowledge_confidence": 1},
    "principiante": {"age": 22, "interest": "less", "inflation": "more", "diversification": "true",
                     "knowledge_confidence": 2, "income_level": 1, "assets_level": 1},
}


def predict_with(client, answers, **changes):
    response = client.post(PREDICT, json={**answers, **changes})
    assert response.status_code == 200
    return response.json()


def test_failed_questions_follow_the_answers(client, answers):
    assert predict_with(client, answers, **PROFILES["experto"])["failed_questions"] == []
    assert predict_with(client, answers, **DONT_KNOW)["failed_questions"] == [
        "interest", "inflation", "diversification"]


def test_overconfidence_is_detected(client, answers):
    assert predict_with(client, answers, **PROFILES["sobreconfiado"])["overconfident"] is True
    assert predict_with(client, answers, **PROFILES["humilde"])["overconfident"] is False


def test_overconfidence_raises_the_risk(client, answers):
    """Mismo perfil sin aciertos: reconocer que no sabe vs creer que sabe (Bawalle et al., 2025)."""
    assert predict_with(client, answers, **PROFILES["humilde"])["category"] == "less_likely"
    assert predict_with(client, answers, **PROFILES["sobreconfiado"])["category"] == "more_likely"


def test_extreme_profiles(client, answers):
    assert predict_with(client, answers, **PROFILES["experto"])["category"] == "less_likely"
    assert predict_with(client, answers, **PROFILES["principiante"])["category"] == "more_likely"


@pytest.mark.parametrize(("age", "warnings"), [
    (18, []), (93, []), (95, ["age_outside_training_range"])])
def test_warns_outside_the_training_ages(client, answers, age, warnings):
    assert predict_with(client, answers, age=age)["warnings"] == warnings


@pytest.mark.parametrize("profile", PROFILES)
def test_factors_are_few_sorted_and_marked_actionable(client, answers, profile):
    factors = predict_with(client, answers, **PROFILES[profile])["top_factors"]
    impacts = [f["impact"] for f in factors]
    assert 1 <= len(factors) <= 4
    assert impacts == sorted(impacts, reverse=True)
    for factor in factors:
        assert factor["actionable"] == (factor["feature"] in ACTIONABLE)


@pytest.mark.parametrize("profile", PROFILES)
def test_never_recommends_buying_or_selling(client, answers, profile):
    """Decreto 661 de 2018: ningún texto de la respuesta dice que compre o venda."""
    factors = predict_with(client, answers, **PROFILES[profile])["top_factors"]
    labels = " ".join(f["label"] for f in factors)
    assert not re.search(r"compr|vend", labels, re.IGNORECASE)


def test_same_person_gets_the_same_answer(client, answers):
    assert predict_with(client, answers) == predict_with(client, answers)
