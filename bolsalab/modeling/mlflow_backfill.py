"""Carga en MLflow las pruebas que ya hicimos, sin volver a entrenar.

Lee reports/benchmark.csv (los 7 modelos del Ciclo 3A) y reports/tuning.csv
(el ajuste por familias) y crea una corrida por prueba, con sus métricas y
parámetros. Si una corrida ya existe en su experimento, la salta: se puede
correr varias veces sin duplicar.

    uv run python -m bolsalab.modeling.mlflow_backfill

Registra donde diga config.MLFLOW_TRACKING_URI (por defecto, mlflow.db en el
proyecto). Para cargar en otro servidor basta con cambiar esa variable.
"""

from datetime import datetime
from pathlib import Path

import pandas as pd
from mlflow.tracking import MlflowClient

from bolsalab.config import MLFLOW_EXPERIMENTS, MLFLOW_TRACKING_URI, PROJ_ROOT
from bolsalab.modeling.train import BENCHMARK_FILE
from bolsalab.modeling.tuning import TUNING_FILE

# Columnas que van como parámetros. Las demás columnas numéricas van como métricas.
PARAMS = ["step", "grid", "best_params", "fold_detail"]


def source_name(path) -> str:
    """Nombre del CSV para la etiqueta "fuente": relativo al proyecto si está dentro."""
    path = Path(path)
    return path.relative_to(PROJ_ROOT).as_posix() if path.is_relative_to(PROJ_ROOT) else path.name


def artifact_location(tracking_uri: str) -> str | None:
    """Dónde guarda MLflow los archivos de un experimento nuevo.

    Con una base local (sqlite), en la carpeta mlruns/ junto a esa base. Con un
    servidor (por ejemplo en AWS), lo decide el servidor.
    """
    if not tracking_uri.startswith("sqlite:///"):
        return None
    return (Path(tracking_uri.removeprefix("sqlite:///")).resolve().parent / "mlruns").as_uri()


def experiment_id(client: MlflowClient, name: str, tracking_uri: str) -> str:
    """Id del experimento; si no existe lo crea."""
    found = client.get_experiment_by_name(name)
    if found:
        return found.experiment_id
    return client.create_experiment(name, artifact_location=artifact_location(tracking_uri))


def log_row(client: MlflowClient, exp_id: str, name: str, row: pd.Series,
            source: str, start: int | None = None) -> None:
    """Crea una corrida con los parámetros y métricas de una fila del CSV."""
    tags = {"fuente": source, "reentrenado": "no"}
    if "reason" in row:
        tags["razon"] = str(row["reason"])
    run_id = client.create_run(exp_id, start_time=start, tags=tags, run_name=name).info.run_id
    for column, value in row.items():
        if column in PARAMS:
            client.log_param(run_id, column, value)
        elif pd.api.types.is_number(value) and pd.notna(value):
            client.log_metric(run_id, column, float(value))
    client.set_terminated(run_id, end_time=start)


def start_time(row: pd.Series) -> int | None:
    """La fecha original de la prueba en milisegundos, o None si el CSV no la tiene."""
    if pd.isna(row.get("run_at")):
        return None
    return int(datetime.fromisoformat(row["run_at"]).timestamp() * 1000)


def load_csv(client: MlflowClient, tracking_uri: str, experiment: str, rows: pd.DataFrame,
             name_column: str, source: str) -> int:
    """Carga las filas nuevas o repetidas después y dice cuántas cargó.

    Una prueba se reconoce por su nombre y su fecha: si se volvió a correr, la
    corrida vieja se reemplaza por la nueva.
    """
    exp_id = experiment_id(client, experiment, tracking_uri)
    runs = {run.info.run_name: run for run in client.search_runs([exp_id], max_results=1000)}
    added = 0
    for _, row in rows.iterrows():
        name, start = row[name_column], start_time(row)
        old = runs.get(name)
        if old and (start is None or old.info.start_time == start):
            continue
        if old:
            client.delete_run(old.info.run_id)
        log_row(client, exp_id, name, row.drop([name_column, "run_at"], errors="ignore"), source, start)
        added += 1
    return added


def backfill(tracking_uri: str = MLFLOW_TRACKING_URI, benchmark_file=BENCHMARK_FILE,
             tuning_file=TUNING_FILE) -> dict:
    """Carga la comparación y el ajuste; devuelve cuántas corridas nuevas hubo en cada uno."""
    client = MlflowClient(tracking_uri)
    # Si una prueba se repitió con --rerun, vale su última corrida.
    tuning = pd.read_csv(tuning_file).drop_duplicates("experiment", keep="last")
    return {
        "comparacion": load_csv(client, tracking_uri, MLFLOW_EXPERIMENTS["comparacion"],
                                pd.read_csv(benchmark_file), "model", source_name(benchmark_file)),
        "ajuste": load_csv(client, tracking_uri, MLFLOW_EXPERIMENTS["ajuste"],
                           tuning, "experiment", source_name(tuning_file)),
    }


def how_to_see(tracking_uri: str) -> str:
    """Cómo abrir las corridas: con una base local hay que levantar la interfaz; con un servidor, basta el navegador."""
    if tracking_uri.startswith("sqlite:///"):
        return f"uv run mlflow ui --backend-store-uri {tracking_uri}"
    return f"abre {tracking_uri} en el navegador"


def main() -> None:
    added = backfill()
    print(f"Corridas nuevas: {added['comparacion']} de la comparación y {added['ajuste']} del ajuste.")
    print(f"Registradas en {MLFLOW_TRACKING_URI}")
    print(f"Para verlas: {how_to_see(MLFLOW_TRACKING_URI)}")


if __name__ == "__main__":
    main()
