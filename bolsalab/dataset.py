"""Etapas 1 y 2 del pipeline: obtención y limpieza de datos.

Una función `descargar_*` por fuente escribe en `data/raw` (o lee de
`data/external` si la fuente es manual). Una función `limpiar_*` por fuente
escribe su tabla limpia en `data/interim`.

Reglas de limpieza obligatorias (ver references/):
- Quitar filas de festivos BVC que Yahoo trae con volumen 0 y precio plano.
- Mapear tickers renombrados (PFBCOLOM -> PFCIBEST).
- Reindexar todo al calendario de días hábiles BVC.
- Unir variables macro por fecha de publicación (as-of), nunca por fecha de corte.

Uso: python -m bolsalab.dataset
"""


def descargar_precios_yfinance() -> None:
    """Precios OHLCV diarios de CLASES_ACTIVO y TICKERS_BVC desde Yahoo Finance."""
    raise NotImplementedError


def descargar_macro_banrep() -> None:
    """TRM, tasa de política, IBR, DTF y TES desde el servicio SDMX del Banco de la República."""
    raise NotImplementedError


def descargar_globales_fred() -> None:
    """Series de FRED_SERIES (VIX, estrés financiero, tasas, petróleo, dólar)."""
    raise NotImplementedError


def descargar_microdatos_encuestas() -> None:
    """Verifica que SCF 2022 e IEFIC 2017-2018 estén en data/external (descarga manual)."""
    raise NotImplementedError


def limpiar() -> None:
    """Aplica las reglas de limpieza y escribe una tabla por fuente en data/interim."""
    raise NotImplementedError


def main() -> None:
    descargar_precios_yfinance()
    descargar_macro_banrep()
    descargar_globales_fred()
    descargar_microdatos_encuestas()
    limpiar()


if __name__ == "__main__":
    main()
