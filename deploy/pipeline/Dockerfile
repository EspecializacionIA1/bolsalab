# Imagen de las etapas del flujo de Airflow en Kubernetes: cada etapa es un pod
# que corre un módulo de bolsalab/ con esta imagen. Se construye desde la raíz:
#   docker build -f deploy/pipeline/Dockerfile -t bolsalab/pipeline:dev .
# Los datos NO van en la imagen (Ley 1581 y licencias): llegan por un volumen
# montado en /app/data, /app/reports y /app/models.
FROM python:3.12-slim

# XGBoost y LightGBM necesitan la librería OpenMP del sistema.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.27 /uv /bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_NO_CACHE=1

WORKDIR /app

# Primero solo las dependencias (uv.lock), para que un cambio de código no las
# reinstale.
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

# El código se instala editable: así bolsalab.config ubica data/, reports/ y
# models/ dentro de /app, donde se monta el volumen.
COPY bolsalab/ bolsalab/
COPY tests/ tests/
RUN uv sync --frozen --no-dev \
    && uv pip install pytest==9.1.1

# Las etapas llaman python y pytest directo del entorno, sin `uv run`, que
# volvería a sincronizar y quitaría pytest.
ENV PATH="/app/.venv/bin:$PATH"

# Corre sin permisos de administrador. HOME en /tmp porque matplotlib y MLflow
# escriben ahí sus cachés.
RUN useradd --system --uid 1000 pipeline
ENV HOME=/tmp MPLCONFIGDIR=/tmp/matplotlib
USER pipeline
