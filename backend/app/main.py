"""API de BolsaLAB.

Expone el modelo de reacción ante caídas. Toda la lógica está en
bolsalab/modeling/predict.py, el mismo código de la app de Streamlit;
aquí solo se recibe, se valida y se responde.

    uv run --group api uvicorn backend.app.main:app --reload
    http://localhost:8000/api/docs
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from backend.app.schemas import Answers, Result
from bolsalab.config import API_RATE_LIMIT, MODEL_ARTIFACT_NAME
from bolsalab.modeling.predict import CrashReactionModel

# Cuenta las peticiones por IP. Detrás de Caddy, uvicorn toma la IP real con --proxy-headers.
limiter = Limiter(key_func=get_remote_address)
model = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    # El modelo se carga una sola vez, al arrancar.
    model["crash"] = CrashReactionModel()
    yield


app = FastAPI(
    title="BolsaLAB API",
    description="Reacción ante caídas del mercado. "
                "Prototipo académico, no es asesoría de inversión.",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)
app.state.limiter = limiter


@app.exception_handler(RateLimitExceeded)
def too_many_requests(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    message = "Demasiadas solicitudes. Intenta de nuevo en un minuto."
    return JSONResponse(status_code=429, content={"detail": message})


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "model_version": MODEL_ARTIFACT_NAME}


@app.post("/api/v1/crash-reaction/predict", response_model=Result)
@limiter.limit(API_RATE_LIMIT)
def predict(request: Request, answers: Answers) -> dict:
    # Las respuestas no se guardan ni se registran (Ley 1581 de 2012).
    return model["crash"].predict(answers.model_dump())
