"""Pruebas de la tabla de desempeño por grupos con datos inventados (no usa la encuesta)."""

import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LogisticRegression

from bolsalab.modeling.groups import group_labels, performance_by_group


@pytest.fixture(scope="module")
def people():
    """600 personas inventadas con las columnas que usan los grupos; vende el ~20 %."""
    rng = np.random.default_rng(0)
    n = 600
    X = pd.DataFrame({
        "male": rng.integers(0, 2, n),
        "age": rng.integers(18, 80, n),
        "income_bracket": rng.integers(1, 13, n),
        "knows_interest": rng.integers(0, 2, n),
        "knows_inflation": rng.integers(0, 2, n),
        "knows_diversification": rng.integers(0, 2, n),
    })
    y = pd.Series((rng.random(n) < 0.2).astype(int))
    return X, y


def test_beginner_is_under_35_with_at_most_one_correct_answer():
    X = pd.DataFrame({
        "male": [1, 0, 1, 0],
        "age": [34, 34, 35, 20],
        "income_bracket": [1, 2, 3, 4],
        "knows_interest": [1, 1, 0, 0],
        "knows_inflation": [0, 1, 0, 0],
        "knows_diversification": [0, 0, 0, 0],
    })
    # 34 con 1 acierto sí; 34 con 2 no; 35 no por edad; 20 con 0 sí
    assert group_labels(X)["Principiantes"].tolist() == ["Sí", "No", "No", "Sí"]


def test_table_includes_beginners(people):
    X, y = people
    table = performance_by_group(LogisticRegression(max_iter=1000), X, y)
    beginners = table[table["grupo"] == "Principiantes"]
    assert set(beginners["valor"]) == {"Sí", "No"}
    assert beginners["personas"].sum() == len(X)
