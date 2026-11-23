"""Flujo 1 de BolsaLAB: de la encuesta al modelo para la app, sin mirar la prueba.

dataset -> validar -> features -> validar -> comparar modelos -> compuerta de calidad
-> exportar prototipo (si el modelo de models/ no es el final) -> grupos y SHAP.

Nunca corre train.py --final: eso vive en bolsalab_prueba_final.
"""

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import dag, task

from bolsalab_comun import (
    DEFAULT_ARGS, ENV, GUARD_FINAL_MODEL, PROJECT_PYTHON, PYTEST, REPO, RUN, SKIP, START_DATE, UV,
)

# Propuesta del equipo, pendiente de registrar en el protocolo.
UMBRALES = {
    "auroc_minimo": 0.60,              # por debajo, algo se rompió en los datos o en el código
    "pendiente_calibracion": (0.8, 1.25),
}


def bash(task_id, command, **kwargs):
    return BashOperator(task_id=task_id, bash_command=command, env=ENV, append_env=True,
                        **kwargs)


@dag(
    dag_id="bolsalab_entrenamiento",
    description="De la encuesta japonesa al modelo de la app, sin mirar la prueba",
    schedule=None,          # a mano o cuando haya datos nuevos; los datos de 2020 no cambian solos
    start_date=START_DATE,
    catchup=False,
    default_args=DEFAULT_ARGS,
    tags=["bolsalab", "entrenamiento"],
)
def bolsalab_entrenamiento():

    # 1. La encuesta tiene que estar: si falta, las pruebas de datos se saltarían en silencio.
    verificar_fuente = bash(
        "verificar_fuente",
        f'cd "{REPO}" && {UV} run python -c "'
        "from bolsalab.config import JAPAN_SURVEY_FILE as f; "
        "assert f.exists(), f'Falta la encuesta: {f}'\"",
    )

    # 2-3. Carga y limpieza, y los valores del protocolo (sección 2).
    preparar_datos = bash("preparar_datos", RUN + "bolsalab.dataset")
    validar_datos = bash("validar_datos", PYTEST + "tests/test_dataset.py")

    # 4-5. Las 17 variables y `sold`.
    construir_variables = bash("construir_variables", RUN + "bolsalab.features")
    validar_variables = bash("validar_variables", PYTEST + "tests/test_features.py")

    # 6. Los 7 modelos con validación anidada 5 x 3. No toca la prueba.
    comparar_modelos = bash("comparar_modelos", RUN + "bolsalab.modeling.train")

    # 7. Reglas de calidad sobre reports/benchmark.csv, en el entorno del proyecto.
    @task.external_python(task_id="compuerta_calidad", python=PROJECT_PYTHON,
                          expect_airflow=False)
    def compuerta_calidad(umbrales: dict) -> dict:
        import pandas as pd

        from bolsalab.modeling.train import BENCHMARK_FILE, MODELS, choose_winner

        benchmark = pd.read_csv(BENCHMARK_FILE)
        faltan = set(MODELS) - set(benchmark["model"])
        if faltan:
            raise ValueError(f"benchmark.csv no tiene estos modelos: {sorted(faltan)}")
        if benchmark[["auroc", "auroc_sd", "calibration_slope"]].isna().any().any():
            raise ValueError("benchmark.csv tiene métricas vacías")

        fila = benchmark.set_index("model")
        ganador = choose_winner(benchmark)
        auroc = fila.loc[ganador, "auroc"]
        pendiente = fila.loc[ganador, "calibration_slope"]

        problemas = []
        if auroc < umbrales["auroc_minimo"]:
            problemas.append(f"AUROC {auroc:.3f} < {umbrales['auroc_minimo']}")
        if ganador != "logistic" and auroc <= fila.loc["logistic", "auroc"]:
            problemas.append("el ganador no supera a la regresión logística")
        lo, hi = umbrales["pendiente_calibracion"]
        if not lo <= pendiente <= hi:
            problemas.append(f"pendiente de calibración {pendiente:.2f} fuera de [{lo}, {hi}]")
        if problemas:
            raise ValueError(f"No pasa la compuerta ({ganador}): " + "; ".join(problemas))

        print(f"Pasa la compuerta: {ganador} con AUROC {auroc:.3f} y pendiente {pendiente:.2f}")
        return {"ganador": ganador, "auroc": float(auroc), "pendiente": float(pendiente)}

    calidad = compuerta_calidad(UMBRALES)

    # 8. Exporta para la app y registra en MLflow, salvo que models/ ya tenga el modelo final.
    exportar_prototipo = bash(
        "exportar_prototipo",
        f'cd "{REPO}" && {UV} run python -c "{GUARD_FINAL_MODEL}" '
        f"&& {UV} run python -m bolsalab.modeling.train --prototype",
        skip_on_exit_code=SKIP,
    )

    # 9-10. Revisiones del modelo que quedó en models/ (corren aunque la exportación se salte).
    desempeno_grupos = bash("desempeno_grupos", RUN + "bolsalab.modeling.groups",
                            trigger_rule="none_failed")
    explicacion_shap = bash("explicacion_shap", RUN + "bolsalab.explain",
                            trigger_rule="none_failed")

    (
        verificar_fuente
        >> preparar_datos >> validar_datos
        >> construir_variables >> validar_variables
        >> comparar_modelos >> calidad
        >> exportar_prototipo >> [desempeno_grupos, explicacion_shap]
    )


bolsalab_entrenamiento()
