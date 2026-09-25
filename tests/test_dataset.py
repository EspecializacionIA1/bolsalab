import pandas as pd

from bolsalab.dataset import parse_banrep_xml, yahoo_tickers

# Respuesta de ejemplo del BanRep: una serie diaria (con un dato vacío) y una mensual
XML_EJEMPLO = b"""<?xml version="1.0" encoding="UTF-8"?>
<message:GenericData xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
    xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic">
  <message:DataSet>
    <generic:Series>
      <generic:SeriesKey>
        <generic:Value id="SUBJECT" value="TRM"/>
        <generic:Value id="UNIT_MEASURE" value="COP"/>
      </generic:SeriesKey>
      <generic:Obs>
        <generic:ObsDimension value="20260921"/>
        <generic:ObsValue value="3192.92"/>
      </generic:Obs>
      <generic:Obs>
        <generic:ObsDimension value="20260922"/>
      </generic:Obs>
    </generic:Series>
    <generic:Series>
      <generic:SeriesKey>
        <generic:Value id="SUBJECT" value="TES10"/>
      </generic:SeriesKey>
      <generic:Obs>
        <generic:ObsDimension value="2026-08"/>
        <generic:ObsValue value="0.1284"/>
      </generic:Obs>
    </generic:Series>
  </message:DataSet>
</message:GenericData>"""


def test_parses_daily_and_monthly_series():
    df = parse_banrep_xml(XML_EJEMPLO)

    assert len(df) == 3
    assert set(df["subject"]) == {"TRM", "TES10"}

    trm = df[df["subject"] == "TRM"].sort_values("date")
    assert trm["date"].dt.strftime("%Y-%m-%d").tolist() == ["2026-09-21", "2026-09-22"]
    assert trm["value"].iloc[0] == 3192.92
    assert pd.isna(trm["value"].iloc[1])  # el dato vacío se conserva, no se borra la fila

    tes = df[df["subject"] == "TES10"]
    assert tes["date"].iloc[0].strftime("%Y-%m") == "2026-08"


def test_xml_without_series_returns_empty():
    assert parse_banrep_xml(b"<root/>").empty


def test_tickers_have_no_duplicates():
    tickers = yahoo_tickers()
    assert len(tickers) == len(set(tickers))
    assert "ICOLCAP.CL" in tickers
    assert "SPY" in tickers

