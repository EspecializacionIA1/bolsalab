"""Descarga de datos (etapa 1)

Cada fuente se guarda tal cual llega en data/raw/<fuente>/ como parquet.
En data/raw/manifest.json queda el registro de qué se bajó, de dónde y cuándo.

Uso:
    uv run python -m bolsalab.dataset               # todas las fuentes
    uv run python -m bolsalab.dataset banrep fred   # solo algunas
"""

import io
import json
import os
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime

import pandas as pd
import requests
import yfinance as yf

from bolsalab.config import (
    ASSET_CLASSES,
    BANREP_FLOWS,
    BANREP_SDMX_URL,
    BVC_TICKERS,
    FRED_SERIES,
    RAW_DATA_DIR,
    START_DATE,
)

MANIFEST = RAW_DATA_DIR / "manifest.json"
SDMX_NS = {"g": "http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"}


def save_raw(df, source, name, url, date_col):
    folder = RAW_DATA_DIR / source
    folder.mkdir(parents=True, exist_ok=True)

    # ECOPETROL.CL -> ECOPETROL_CL para no tener problemas con el nombre de archivo
    file_name = name.replace(".", "_")
    df.to_parquet(folder / f"{file_name}.parquet", index=False)

    dates = pd.to_datetime(df[date_col])
    start, end = dates.min().date(), dates.max().date()
    print(f"  {source}/{file_name}: {len(df)} filas, {start} a {end}")

    # Registro para poder decir de dónde sale cada cifra
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    manifest[f"{source}/{file_name}"] = {
        "url": url,
        "rows": len(df),
        "start": str(start),
        "end": str(end),
        "downloaded_at": datetime.now().isoformat(timespec="seconds"),
    }
    MANIFEST.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def with_retries(func, *args):
    # Los servidores a veces no responden a la primera (al BanRep le pasa mucho, temas de timeout).
    # Reintenta hasta 3 veces con 5 segundos de espera.
    for attempt in range(3):
        try:
            return func(*args)
        except Exception as error:
            if attempt == 2:
                raise
            print(f"  falló ({error}), reintentando...")
            time.sleep(5)


# ---------- Yahoo Finance ----------

def yahoo_tickers():
    tickers = [a["ticker"] for a in ASSET_CLASSES.values() if a["source"] == "yfinance"]
    tickers += BVC_TICKERS
    return list(dict.fromkeys(tickers))  # quita repetidos sin cambiar el orden


def fetch_ticker(ticker):
    # auto_adjust=False para tener el cierre real y el ajustado por separado
    df = yf.download(ticker, start=START_DATE, auto_adjust=False, actions=True,
                     progress=False, multi_level_index=False)
    if df.empty:
        raise ValueError("Yahoo no devolvió datos")
    df = df.reset_index()
    df.columns = [str(c).lower().replace(" ", "_") for c in df.columns]
    df.insert(0, "ticker", ticker)
    return df


def download_yahoo():
    for ticker in yahoo_tickers():
        try:
            df = with_retries(fetch_ticker, ticker)
        except Exception as error:
            print(f"  ERROR {ticker}: {error}")
            continue
        save_raw(df, "yfinance", ticker, f"https://finance.yahoo.com/quote/{ticker}", "date")
        time.sleep(2)  # si se piden muchos seguidos Yahoo bloquea por un rato


# ---------- Banco de la República ----------

def parse_banrep_xml(xml):
    # El BanRep solo responde en XML (SDMX). Lo paso a una tabla con una fila por dato.
    rows = []
    for series in ET.fromstring(xml).iterfind(".//g:Series", SDMX_NS):
        # Datos de la serie: subject, unit_measure, etc.
        info = {v.get("id").lower(): v.get("value")
                for v in series.iterfind("g:SeriesKey/g:Value", SDMX_NS)}
        for obs in series.iterfind("g:Obs", SDMX_NS):
            value = obs.find("g:ObsValue", SDMX_NS)
            rows.append({
                **info,
                "date": obs.find("g:ObsDimension", SDMX_NS).get("value"),
                "value": float(value.get("value")) if value is not None else None,
            })

    df = pd.DataFrame(rows)
    if not df.empty:
        # Las diarias vienen como 20260922 y las mensuales como 2026-08
        df["date"] = pd.to_datetime(df["date"], format="mixed")
    return df


def fetch_banrep_series(url):
    # Solo filtra por año y el año final no se incluye, por eso se pide hasta el próximo
    start_year = START_DATE[:4]
    end_year = datetime.now().year + 1
    response = requests.get(url, params={"startPeriod": start_year, "endPeriod": end_year},
                            timeout=90)
    response.raise_for_status()
    df = parse_banrep_xml(response.content)
    if df.empty:
        raise ValueError("el BanRep no devolvió datos")
    return df


def download_banrep():
    # Ojo: los TES vienen en fracción (0.1284 = 12,84 %)
    for name, flow in BANREP_FLOWS.items():
        url = f"{BANREP_SDMX_URL}/ESTAT,{flow},1.0/all/ALL/"
        try:
            df = with_retries(fetch_banrep_series, url)
        except Exception as error:
            print(f"  ERROR {name}: {error}")
            continue
        save_raw(df, "banrep", name, url, "date")


# ---------- FRED ----------

def fetch_fred_series(series_id):
    # Si hay FRED_API_KEY en el .env uso la API oficial, si no el CSV público
    api_key = os.getenv("FRED_API_KEY")
    if api_key:
        response = requests.get("https://api.stlouisfed.org/fred/series/observations",
                                params={"series_id": series_id, "api_key": api_key,
                                        "file_type": "json", "observation_start": START_DATE},
                                timeout=90)
        response.raise_for_status()
        df = pd.DataFrame(response.json()["observations"])[["date", "value"]]
    else:
        response = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv",
                                params={"id": series_id, "cosd": START_DATE}, timeout=90)
        response.raise_for_status()
        df = pd.read_csv(io.StringIO(response.text))
        df.columns = ["date", "value"]

    return pd.DataFrame({
        "date": pd.to_datetime(df["date"]),
        "value": pd.to_numeric(df["value"], errors="coerce"),  # los días sin dato vienen con "."
        "series": series_id,
    })


def download_fred():
    for series_id in FRED_SERIES:
        try:
            df = with_retries(fetch_fred_series, series_id)
        except Exception as error:
            print(f"  ERROR {series_id}: {error}")
            continue
        save_raw(df, "fred", series_id, f"https://fred.stlouisfed.org/series/{series_id}", "date")


SOURCES = {
    "yfinance": download_yahoo,
    "banrep": download_banrep,
    "fred": download_fred,
}


def main():
    # La consola de Windows daña las tildes si no se fuerza utf-8
    sys.stdout.reconfigure(encoding="utf-8")

    selected = sys.argv[1:] or list(SOURCES)
    for source in selected:
        if source not in SOURCES:
            print(f"Fuente '{source}' no existe. Opciones: {', '.join(SOURCES)}")
            continue
        print(f"Descargando {source}...")
        SOURCES[source]()
    print(f"Listo. Registro en {MANIFEST}")


if __name__ == "__main__":
    main()
