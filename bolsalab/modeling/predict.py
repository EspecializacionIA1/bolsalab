"""Carga del modelo publicado y predicción."""

from pathlib import Path


class ProfileModel:
    def __init__(self, artifact_path: str | Path):
        raise NotImplementedError

    def predict(self, answers: dict) -> dict:
        raise NotImplementedError
