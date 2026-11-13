"""Pruebas del análisis bivariado con datos inventados (no usa la encuesta)."""

import pandas as pd
import pytest

from bolsalab.exploration import cross, information_value, sell_rate, summary, surprising_cells


@pytest.fixture
def people():
    """200 personas: 100 hombres que venden el 40 % y 100 mujeres que venden el 10 %.

    `coin` parte a cada grupo por la mitad sin cambiar la venta: no informa.
    """
    rows = []
    for male, sellers in [(1, 40), (0, 10)]:
        for i in range(100):
            rows.append({"male": male, "coin": i % 2, "sold": int(i < sellers)})
    return pd.DataFrame(rows)


def test_sell_rate_counts_people_and_percentage(people):
    table = sell_rate(people, "male")
    assert table.loc[1, "personas"] == 100
    assert table.loc[1, "vendió (%)"] == 40
    assert table.loc[0, "vendió (%)"] == 10


def test_information_value_is_zero_when_the_variable_does_not_separate(people):
    assert information_value(people, "coin") == pytest.approx(0)
    assert information_value(people, "male") > 0.3


def test_summary_orders_by_difference_and_ignores_small_groups(people):
    table = summary(people, ["coin", "male"], min_people=50)
    assert list(table["variable"]) == ["male", "coin"]
    assert table.loc[0, "diferencia"] == 30
    assert table.loc[0, "grupo que más vende"] == 1

    people.loc[len(people)] = {"male": 2, "coin": 0, "sold": 1}
    assert summary(people, ["male"], min_people=50).loc[0, "vende más (%)"] == 40


def test_cross_hides_cells_with_few_people(people):
    assert cross(people, "male", "coin", min_people=50).loc[1, 0] == 40
    assert cross(people, "male", "coin", min_people=51).isna().all().all()


def test_surprise_is_zero_when_the_two_variables_only_add_up(people):
    table = surprising_cells(people, ["male", "coin"], min_people=50)
    assert len(table) == 4
    assert table["sorpresa"].abs().max() == pytest.approx(0)
