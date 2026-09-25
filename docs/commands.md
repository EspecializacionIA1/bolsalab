# Comandos

Todos se ejecutan desde la raíz del repositorio (`bolsalab/`), en PowerShell o en cualquier terminal.

## Preparar el entorno

Solo la primera vez, o cuando cambie `uv.lock`:

```
uv sync
```

Crear el archivo de variables de entorno (una sola vez):

```
cp .env.example .env
```

## Descargar datos

Todas las fuentes (Yahoo, Banco de la República y FRED), toma 1-2 minutos:

```
uv run python -m bolsalab.dataset
```

Solo algunas fuentes:

```
uv run python -m bolsalab.dataset yfinance
uv run python -m bolsalab.dataset banrep
uv run python -m bolsalab.dataset fred
uv run python -m bolsalab.dataset banrep fred
```

Los datos quedan en `data/raw/<fuente>/` y el registro de descargas en `data/raw/manifest.json`.

La descarga funcionó si:
- aparecen 19 líneas (7 de Yahoo, 6 del BanRep y 6 de FRED);
- ninguna dice `ERROR`;
- las fechas llegan hasta ayer u hoy.

Si aparece `falló (...), reintentando...` seguido de la línea normal, todo está bien: el servidor tardó y el reintento lo resolvió.

## Revisar los datos descargados

Listar los archivos:

```
dir data\raw\yfinance, data\raw\banrep, data\raw\fred
```

Ver los últimos días de una serie:

```
uv run python -c "import pandas as pd; print(pd.read_parquet('data/raw/banrep/trm.parquet')[['date','value']].tail())"
uv run python -c "import pandas as pd; print(pd.read_parquet('data/raw/yfinance/ICOLCAP_CL.parquet')[['date','close','volume']].tail())"
uv run python -c "import pandas as pd; print(pd.read_parquet('data/raw/fred/VIXCLS.parquet').tail())"
```

Comparar la TRM con la fuente oficial (Superintendencia Financiera). El último valor debe coincidir:
https://www.datos.gov.co/resource/32sa-8pi3.json?$order=vigenciadesde%20DESC&$limit=3

## Pruebas y calidad del código

Tests:

```
uv run pytest tests -v
```

Revisión de estilo y errores (linter):

```
uv run ruff check bolsalab tests
```

Corregir automáticamente lo que se pueda:

```
uv run ruff check bolsalab tests --fix
```

## Dependencias

Agregar una librería (actualiza `pyproject.toml` y `uv.lock`):

```
uv add <paquete>
```

Agregar una herramienta solo de desarrollo:

```
uv add --dev <paquete>
```

Abrir Jupyter con el entorno del proyecto:

```
uv run jupyter lab
```
