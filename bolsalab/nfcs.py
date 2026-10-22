"""Tabla de la NFCS 2018 (EE. UU.) para el dataset multipaís.

Une las dos partes de la encuesta por persona, deja a quien respondió qué hizo
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

# D20: "Cuando la bolsa cayó 10 % a comienzos de febrero, ¿qué hizo?"
BOUGHT, SOLD, NEITHER = 1, 2, 3
DONT_KNOW, PREFER_NOT_TO_SAY = 98, 99


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


def main() -> None:
    respondents = select_respondents(load_nfcs_2018())
    sold = build_target(respondents)
    print(f"{len(respondents)} personas; vendieron {sold.sum()} ({sold.mean():.1%})")


if __name__ == "__main__":
    main()
