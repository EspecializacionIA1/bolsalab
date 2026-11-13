"""Análisis bivariado: cómo cambia la venta según cada respuesta de la encuesta.

Sirve para decidir qué variables nuevas vale la pena probar, antes de entrenar.
Usa solo el 80 % de entrenamiento; el 20 % de prueba no se mira. No entrena
modelos. Lo usa el notebook "Exploración de variables".

Método: Guyon y Elisseeff (2003) para mirar cada variable frente al resultado,
y Siddiqi (2006) para el valor de información (IV).
"""

from itertools import combinations

import numpy as np
import pandas as pd

from bolsalab.features import TRAINING_FILE
from bolsalab.modeling.train import split_data

# Un grupo con menos personas no cuenta: su porcentaje puede ser casualidad.
# Decisión nuestra.
MIN_PEOPLE = 500

QUESTIONS = ["knows_interest", "knows_inflation", "knows_diversification"]

# La edad se mira por décadas; edad por edad hay grupos de 1 a 5 personas.
AGE_EDGES = [0, 20, 30, 40, 50, 60, 70, 80, 200]
AGE_LABELS = ["<20", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80+"]

# Las 16 variables: las 17 del modelo sin age_squared, que repite a la edad.
VARIABLES = [*QUESTIONS, "knowledge_confidence", "overconfidence", "age_group", "male",
             "university", "married", "has_children", "urban", "employed",
             "income_bracket", "assets_bracket", "risk_aversion", "short_term_view"]


def load_training_people() -> pd.DataFrame:
    """Las 43.763 personas de entrenamiento, con `sold` y la edad por décadas."""
    table = pd.read_parquet(TRAINING_FILE)
    X_train, _, y_train, _ = split_data(table)
    people = X_train.assign(sold=y_train)
    people["age_group"] = pd.cut(people["age"], AGE_EDGES, labels=AGE_LABELS, right=False)
    return people


def sell_rate(people: pd.DataFrame, column: str) -> pd.DataFrame:
    """Cuántas personas hay en cada respuesta y qué porcentaje vendió.

     la variable en filas, y `sold` como cuenta y
    como promedio. El promedio de unos y ceros es el porcentaje que vendió.
    """
    groups = people.groupby(column, observed=True)["sold"]
    return pd.DataFrame({"personas": groups.size(), "vendió (%)": groups.mean() * 100})


def information_value(people: pd.DataFrame, column: str) -> float:
    """Valor de información (IV): qué tan bien separa la variable a quienes vendieron.

    Compara, grupo por grupo, qué parte de los que vendieron cae ahí frente a
    qué parte de los que no vendieron. Si las dos partes son iguales en todos
    los grupos, el IV es 0: la variable no separa. Siddiqi (2006): menos de
    0,02 no sirve; 0,02 a 0,1 débil; 0,1 a 0,3 media; más de 0,3 fuerte.
    """
    groups = people.groupby(column, observed=True)["sold"]
    sold, total = groups.sum(), groups.size()
    share_of_sellers = sold / sold.sum()
    share_of_holders = (total - sold) / (total - sold).sum()
    both = (share_of_sellers > 0) & (share_of_holders > 0)
    sellers, holders = share_of_sellers[both], share_of_holders[both]
    return float(((sellers - holders) * np.log(sellers / holders)).sum())


def summary(people: pd.DataFrame, columns=VARIABLES, min_people: int = MIN_PEOPLE) -> pd.DataFrame:
    """Una fila por variable: el grupo que más vende, el que menos, la diferencia y el IV.

    Los grupos con menos de min_people personas no entran al máximo ni al
    mínimo. Es la hoja "Resumen" del Excel, más la columna IV.
    """
    rows = []
    for column in columns:
        rate = sell_rate(people, column)
        big_groups = rate.loc[rate["personas"] >= min_people, "vendió (%)"]
        rows.append({
            "variable": column,
            "vende más (%)": big_groups.max(), "grupo que más vende": big_groups.idxmax(),
            "vende menos (%)": big_groups.min(), "grupo que menos vende": big_groups.idxmin(),
            "diferencia": big_groups.max() - big_groups.min(),
            "IV": information_value(people, column),
        })
    return pd.DataFrame(rows).sort_values("diferencia", ascending=False, ignore_index=True)


def cross(people: pd.DataFrame, rows: str, columns: str,
          min_people: int = MIN_PEOPLE) -> pd.DataFrame:
    """Porcentaje que vendió en cada combinación de dos variables.

    Es la tabla dinámica con una variable en filas y otra en columnas. Las
    casillas con menos de min_people personas quedan vacías.
    """
    cells = people.groupby([rows, columns], observed=True)["sold"]
    rate = (cells.mean() * 100).where(cells.size() >= min_people)
    return rate.unstack(columns)


def surprising_cells(people: pd.DataFrame, columns,
                     min_people: int = MIN_PEOPLE) -> pd.DataFrame:
    """Combinaciones de dos respuestas que venden distinto a lo esperado.

    Lo esperado es lo que vendería la casilla si las dos pistas solo se
    sumaran: venta de la respuesta 1 + venta de la respuesta 2 - venta general.
    La sorpresa es lo observado menos lo esperado. Una sorpresa grande dice que
    juntas las dos respuestas cuentan algo que por separado no cuentan.
    """
    overall = people["sold"].mean() * 100
    found = []
    for first, second in combinations(columns, 2):
        cells = people.groupby([first, second], observed=True)["sold"].agg(
            personas="size", vendio="mean").reset_index()
        cells = cells[cells["personas"] >= min_people]
        rate_first = sell_rate(people, first)["vendió (%)"]
        rate_second = sell_rate(people, second)["vendió (%)"]
        expected = (cells[first].map(rate_first).astype(float)
                    + cells[second].map(rate_second).astype(float) - overall)
        found.append(pd.DataFrame({
            "variable 1": first, "respuesta 1": cells[first].astype(str),
            "variable 2": second, "respuesta 2": cells[second].astype(str),
            "personas": cells["personas"],
            "vendió (%)": cells["vendio"] * 100,
            "esperado (%)": expected,
        }))
    table = pd.concat(found, ignore_index=True)
    table["sorpresa"] = table["vendió (%)"] - table["esperado (%)"]
    order = table["sorpresa"].abs().sort_values(ascending=False).index
    return table.loc[order].reset_index(drop=True)
