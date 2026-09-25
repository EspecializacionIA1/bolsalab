"""Configuración central: rutas, universo de activos, fuentes y semillas.

Todo módulo del pipeline importa sus rutas y parámetros desde aquí para que
ningún valor quede repetido o escrito a mano en notebooks o scripts.
"""

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# --- Rutas (estructura Cookiecutter Data Science) ---------------------------
PROJ_ROOT = Path(__file__).resolve().parents[1]

DATA_DIR = PROJ_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"            # descargas automáticas, tal cual llegan
EXTERNAL_DATA_DIR = DATA_DIR / "external"  # cargas manuales: COLCAP BVC, SCF, IEFIC
INTERIM_DATA_DIR = DATA_DIR / "interim"    # tablas limpias por fuente
PROCESSED_DATA_DIR = DATA_DIR / "processed"  # datasets finales de entrenamiento

MODELS_DIR = PROJ_ROOT / "models"
REPORTS_DIR = PROJ_ROOT / "reports"
FIGURES_DIR = REPORTS_DIR / "figures"

# --- Reproducibilidad ---------------------------------------------------------
RANDOM_STATE = 42
START_DATE = "2010-01-01"

# --- Universo de activos: una serie por clase del portafolio -----------------
# Yahoo Finance usa el sufijo .CL para la Bolsa de Valores de Colombia (no .CO).
ASSET_CLASSES = {
    "colombian_equity": {"source": "yfinance", "ticker": "ICOLCAP.CL"},
    "global_equity": {"source": "yfinance", "ticker": "SPY"},
    "cop_fixed_income": {"source": "banrep", "series": "DF_TES_MONTHLY_HIST"},
    "cash": {"source": "banrep", "series": "DF_IBR_DAILY_HIST"},
}

# Acciones BVC líquidas del COLCAP.
# PFBCOLOM ya no existe: tras la reorganización de Grupo Cibest se usa PFCIBEST.
BVC_TICKERS = ["ECOPETROL.CL", "CIBEST.CL", "PFCIBEST.CL", "ISA.CL", "GEB.CL"]

# --- Series oficiales ---------------------------------------------------------
BANREP_SDMX_URL = "https://totoro.banrep.gov.co/nsi-jax-ws/rest/data"
BANREP_FLOWS = {
    "trm": "DF_TRM_DAILY_HIST",
    "policy_rate": "DF_CBR_DAILY_HIST",
    "ibr": "DF_IBR_DAILY_HIST",
    "dtf": "DF_DTF_DAILY_HIST",
    "tes": "DF_TES_MONTHLY_HIST",
    "colcap_monthly": "DF_COLCAP_MONTHLY_HIST",
}
TRM_DATOS_GOV_URL = "https://www.datos.gov.co/resource/32sa-8pi3.json"

FRED_SERIES = ["VIXCLS", "VXEEMCLS", "STLFSI4", "DGS10", "DCOILBRENTEU", "DTWEXBGS"]

# --- Clasificador de perfil ---------------------------------------------------
# Los nombres de las clases quedan en español porque son los que ve el usuario
RISK_PROFILES = {0: "conservador", 1: "moderado", 2: "agresivo"}
