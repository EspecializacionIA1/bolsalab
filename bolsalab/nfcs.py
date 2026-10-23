"""Tabla de la NFCS 2018 (EE. UU.) para el dataset multipaís.

Une las dos partes de la encuesta por persona,  deja a quien respondió qué hizo
en la caída de febrero de 2018 y construye `sold` con la misma definición de
Japón. 

Uso: uv run python -m bolsalab.nfcs
"""

import zipfile
from pathlib import Path

import pandas as pd

from bolsalab.config import NFCS_INVESTOR_ZIP, NFCS_STATE_ZIP, PROCESSED_DATA_DIR
from bolsalab.features import FEATURES, TRAINING_FILE

# Se guarda solo en el computador de cada integrante: data/ no se sube al repo.
NFCS_TABLE_FILE = PROCESSED_DATA_DIR / "nfcs_table.parquet"

# Variables de Japón que la NFCS no pregunta.
MISSING_IN_NFCS = ["urban", "short_term_view"]
NFCS_FEATURES = [f for f in FEATURES if f not in MISSING_IN_NFCS]

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

# M4: "Del 1 al 7,cómo califica su conocimiento sobre finanzas?". La pasamos
# a la escala de Japón (1 a 5) en proporción, redondeando.
CONFIDENCE_1_TO_5 = {1: 1, 2: 2, 3: 2, 4: 3, 5: 4, 6: 4, 7: 5}

# J2: "Al pensar en sus inversiones, ¿qué tan dispuesto está a asumir riesgos?"
# de 1 (nada) a 10 (muy dispuesto). En Japón va de 0 a 1 y al revés.
RISK_ANSWERS = range(1, 11)

# B4 (parte de inversionistas): valor de las inversiones fuera de cuentas de
# retiro, en 10 tramos de dólares.
ASSET_ANSWERS = range(1, 11)


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
    """Deja a quien dijo qué hizo en la caída y calificó su conocimiento.

    Todos tienen inversiones fuera de retiro, porque la encuesta descartaba al
    resto (pregunta A3). No se filtra por lo que tenían en julio (B2), porque
    eso ya depende de si vendieron en febrero. Descartamos a quien no calificó su
    conocimiento (M4), su disposición al riesgo (J2) o el valor de sus
    inversiones (B4), porque en Japón esas preguntas no tienen "no sabe".
    """
    keep = (survey["D20"].isin([BOUGHT, SOLD, NEITHER])
            & survey["M4"].isin(CONFIDENCE_1_TO_5)
            & survey["J2"].isin(RISK_ANSWERS)
            & survey["B4_inv"].isin(ASSET_ANSWERS))
    return survey[keep].reset_index(drop=True)


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


def build_confidence(respondents: pd.DataFrame, knowledge: pd.DataFrame) -> pd.DataFrame:
    """Devuelve la confianza (1 a 5) y el exceso de confianza con la regla de Japón.

     En el archivo japonés hay exceso de confianza si la persona marcó 5, o si
    marcó 4 y acertó 2 o menos de las 3 preguntas
    """
    confidence = respondents["M4"].map(CONFIDENCE_1_TO_5)
    correct = knowledge.sum(axis=1)
    overconfidence = confidence.eq(5) | (confidence.eq(4) & correct.le(2))
    return pd.DataFrame({
        "knowledge_confidence": confidence,
        "overconfidence": overconfidence.astype(int),
    })


def build_risk_aversion(respondents: pd.DataFrame) -> pd.Series:
    """Devuelve `risk_aversion` de 0 a 1: 1 = nada dispuesto al riesgo, 0 = muy dispuesto."""
    return ((10 - respondents["J2"]) / 9).rename("risk_aversion")

def match_brackets_by_position(source: pd.Series, target: pd.Series) -> dict:
    """Asigna a cada tramo de `source` el tramo de `target` en la misma posición.

    La posición de un tramo es la mitad de su franja en la distribución
    acumulada de su país. Por ejemplo, un tramo que va del 24 % al 47 % de la
    gente queda en el 36 %, y se le asigna el tramo de `target` que contiene
    ese 36 %.
    """
    source_share = source.value_counts(normalize=True).sort_index().cumsum()
    target_share = target.value_counts(normalize=True).sort_index().cumsum()
    mapping, start = {}, 0.0
    for bracket, end in source_share.items():
        middle = (start + end) / 2
        mapping[int(bracket)] = int(target_share.index[(target_share >= middle).argmax()])
        start = end
    return mapping


def build_income(respondents: pd.DataFrame, japan_income: pd.Series) -> pd.Series:
    """Devuelve `income_bracket` en tramos japoneses, por posición dentro de cada país."""
    mapping = match_brackets_by_position(respondents["A8"], japan_income)
    return respondents["A8"].map(mapping).rename("income_bracket")

def build_assets(respondents: pd.DataFrame, japan_assets: pd.Series) -> pd.Series:
    """Devuelve `assets_bracket` en tramos japoneses, por posición dentro de cada país."""
    mapping = match_brackets_by_position(respondents["B4_inv"], japan_assets)
    return respondents["B4_inv"].map(mapping).rename("assets_bracket")

def build_table(respondents: pd.DataFrame, japan: pd.DataFrame) -> pd.DataFrame:
    """Devuelve la tabla final: las 15 variables en el orden de Japón y `sold`.

    `japan` es la tabla de entrenamiento japonesa; se usa para convertir los
    tramos de ingreso y de inversiones por posición.
    """
    knowledge = build_knowledge(respondents)
    table = pd.concat([
        build_demographics(respondents),
        knowledge,
        build_confidence(respondents, knowledge),
        build_risk_aversion(respondents),
        build_income(respondents, japan["income_bracket"]),
        build_assets(respondents, japan["assets_bracket"]),
    ], axis=1)
    return table[NFCS_FEATURES].assign(sold=build_target(respondents))


def main() -> None:
    respondents = select_respondents(load_nfcs_2018())
    japan = pd.read_parquet(TRAINING_FILE, columns=["income_bracket", "assets_bracket"])
    table = build_table(respondents, japan)
    table.to_parquet(NFCS_TABLE_FILE, index=False)
    print(f"{len(table)} personas y {len(NFCS_FEATURES)} variables guardadas en {NFCS_TABLE_FILE}")
    print(f"Vendieron {table['sold'].sum()} ({table['sold'].mean():.1%})")

if __name__ == "__main__":
    main()
