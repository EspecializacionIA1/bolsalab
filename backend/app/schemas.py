"""Contrato de la API: qué recibe y qué devuelve.

Pydantic valida cada petición antes de llegar al modelo. Si algo no cumple,
FastAPI responde 422 con el detalle del campo que falló.
"""

from typing import Literal

from pydantic import BaseModel, Field


class Answers(BaseModel):
    """Respuestas del cuestionario, con los nombres que espera predict.py."""

    age: int = Field(ge=18, le=100, examples=[27])
    male: bool = Field(examples=[False])
    university: bool = Field(examples=[True])
    married: bool = Field(examples=[False])
    has_children: bool = Field(examples=[False])
    urban: bool = Field(examples=[True])
    employed: bool = Field(examples=[True])
    income_level: int = Field(ge=1, le=5, description="1 bajo a 5 alto, frente a la gente del país",
                              examples=[3])
    assets_level: int = Field(ge=1, le=5, description="1 bajo a 5 alto, frente a la gente del país",
                              examples=[1])
    knowledge_confidence: int = Field(ge=1, le=5, description="Qué tanto cree saber de finanzas",
                                      examples=[4])
    interest: Literal["more", "exactly", "less", "dont_know"] = Field(examples=["more"])
    inflation: Literal["more", "same", "less", "dont_know"] = Field(examples=["dont_know"])
    diversification: Literal["true", "false", "dont_know"] = Field(examples=["false"])


class Factor(BaseModel):
    """Una respuesta que pesó en el resultado."""

    feature: str
    label: str
    direction: Literal["increases", "decreases"]
    impact: float
    actionable: bool


class Result(BaseModel):
    """Lo que ve el frontend. Sin probability ni base_rate: la app nunca muestra la probabilidad."""

    model_version: str
    category: Literal["less_likely", "similar", "more_likely"]
    top_factors: list[Factor]
    failed_questions: list[str]
    overconfident: bool
    not_asked: list[str]
    warnings: list[str]
