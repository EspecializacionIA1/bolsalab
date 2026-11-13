"""Pruebas de la tabla de interacciones SHAP con valores inventados (no usa el modelo)."""

import numpy as np

from bolsalab.explain import interaction_table, join_age_interactions

COLUMNS = ["male", "age", "age_squared"]


def cube(pairs: dict) -> np.ndarray:
    """Dos personas con los mismos SHAP de interacción; cada par va en sus dos mitades."""
    values = np.zeros((2, len(COLUMNS), len(COLUMNS)))
    for (first, second), half in pairs.items():
        a, b = COLUMNS.index(first), COLUMNS.index(second)
        values[:, a, b] = values[:, b, a] = half
    return values


def test_strongest_pair_goes_first_and_adds_both_halves():
    values = cube({("male", "age"): 0.3, ("male", "age_squared"): -0.1})
    table = interaction_table(values, COLUMNS)
    assert list(table.loc[0, ["variable 1", "variable 2"]]) == ["male", "age"]
    assert table.loc[0, "fuerza"] == 0.6
    assert table.loc[1, "fuerza"] == 0.2


def test_age_squared_is_added_to_age():
    values = cube({("male", "age"): 0.3, ("male", "age_squared"): 0.1})
    joined, columns = join_age_interactions(values, COLUMNS)
    assert columns == ["male", "age"]
    table = interaction_table(joined, columns)
    assert len(table) == 1
    assert table.loc[0, "fuerza"] == 0.8
