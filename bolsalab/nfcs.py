"""Tabla de la NFCS 2018 (EE. UU.) para el dataset multipaís.

Une las dos partes de la encuesta por persona,  deja a quien respondió qué hizo
en la caída de febrero de 2018 y construye `sold` con la misma definición de
Japón. 

Uso: uv run python -m bolsalab.nfcs
"""

import zipfile
from pathlib import Path

import pandas as pd

from bolsalab.config import NFCS_INVESTOR_ZIP, NFCS_STATE_ZIP

INVESTOR_CSV = "NFCS 2018 Investor Data 191107.csv"
STATE_CSV = "NFCS 2018 State Data 190603.csv"

# D20: "Cuando la bolsa cayó 10 % a comienzos de febrero, qué hizo?"
BOUGHT, SOLD, NEITHER = 1, 2, 3
DONT_KNOW, PREFER_NOT_TO_SAY = 98, 99

# A3Ar_w: el archivo público solo trae la edad en 6 rangos. Usamos el punto
# medio de cada rango; para "65 o más" fijamos 70.
AGE_BY_RANGE = {1: 21, 2: 29.5, 3: 39.5, 4: 49.5, 5: 59.5, 6: 70}

# A5_2015: 6 = pregrado, 7 = posgrado. El técnico de 2 años (5) no cuenta.
UNIVERSITY_CODES = [6, 7]
# A11: 1 a 4 = hijos que dependen de la persona; 5 = hijos que ya no
# dependen; 6 = no tiene hijos.
NO_CHILDREN = 6
# A9: 1 = independiente, 2 = tiempo completo, 3 = medio tiempo.
EMPLOYED_CODES = [1, 2, 3]

DEMOGRAPHICS = ["age", "age_squared", "male", "university", "married",
                "has_children", "employed"]

# Las tres preguntas de conocimiento (sección M) y su respuesta correcta.
# "No sabe" (98) y "prefiere no decir" (99) cuentan como no acertó.
KNOWLEDGE_ANSWERS = {
    "knows_interest": ("M6", 1),         # más de $102
    "knows_inflation": ("M7", 3),        # menos que hoy
    "knows_diversification": ("M10", 2), # falso
}


def read_csv_from_zip(zip_path: Path, csv_name: str) -> pd.DataFrame:
    """Lee un CSV dentro del zip original, sin descomprimirlo en disco."""
    with zipfile.ZipFile(zip_path) as archive, archive.open(csv_name) as file:
        return pd.read_csv(file, encoding="latin1", low_memory=False)


def load_nfcs_2018(investor_zip: Path = NFCS_INVESTOR_ZIP,
                   state_zip: Path = NFCS_STATE_ZIP) -> pd.DataFrame:
    """Une la parte de inversionistas con la parte State-by-State por NFCSID.

    Algunas preguntas tienen el mismo código en las dos partes pero preguntan
    cosas distintas (A3 es "tiene inversiones fuera de retiro?" en una y
    "sexo" en la otra). Por eso esas columnas llevan el sufijo de su parte:
    _inv o _state.
    """
    investors = read_csv_from_zip(investor_zip, INVESTOR_CSV)
    state = read_csv_from_zip(state_zip, STATE_CSV)
    return investors.merge(state, on="NFCSID", how="left", suffixes=("_inv", "_state"),
                           validate="one_to_one")


def select_respondents(survey: pd.DataFrame) -> pd.DataFrame:
    """Deja a quien dijo qué hizo en la caída: compró, vendió o ninguna.

    Todos tienen inversiones fuera de retiro, porque la encuesta descartaba al
    resto (pregunta A3). No se filtra por lo que tenían en julio (B2), porque
    eso ya depende de si vendieron en febrero.
    """
    return survey[survey["D20"].isin([BOUGHT, SOLD, NEITHER])].reset_index(drop=True)


def build_target(respondents: pd.DataFrame) -> pd.Series:
    """Devuelve `sold`: 1 si vendió; 0 si compró o no hizo ninguna de las dos."""
    return respondents["D20"].eq(SOLD).astype(int).rename("sold")


def build_demographics(respondents: pd.DataFrame) -> pd.DataFrame:
    """Devuelve los datos personales con los nombres y la forma de Japón."""
    age = respondents["A3Ar_w"].map(AGE_BY_RANGE)
    return pd.DataFrame({
        "age": age,
        "age_squared": age ** 2,
        "male": respondents["A3_state"].eq(1).astype(int),
        "university": respondents["A5_2015"].isin(UNIVERSITY_CODES).astype(int),
        "married": respondents["A6"].eq(1).astype(int),
        "has_children": respondents["A11"].ne(NO_CHILDREN).astype(int),
        "employed": respondents["A9"].isin(EMPLOYED_CODES).astype(int),
    })[DEMOGRAPHICS]


def build_knowledge(respondents: pd.DataFrame) -> pd.DataFrame:
    """Devuelve las tres preguntas de conocimiento: 1 si acertó, 0 si no."""
    return pd.DataFrame({
        name: respondents[column].eq(correct).astype(int)
        for name, (column, correct) in KNOWLEDGE_ANSWERS.items()
    })


def main() -> None:
    respondents = select_respondents(load_nfcs_2018())
    sold = build_target(respondents)
    print(f"{len(respondents)} personas; vendieron {sold.sum()} ({sold.mean():.1%})")
    print(build_demographics(respondents).describe().loc[["mean", "min", "max"]].round(2))


if __name__ == "__main__":
    main()
