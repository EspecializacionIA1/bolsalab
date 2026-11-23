"""Flujo 1 de BolsaLAB en Kubernetes: de la encuesta al modelo para la app, sin mirar la prueba.

Las mismas etapas y el mismo orden que dags/bolsalab_entrenamiento.py (el flujo
local), pero cada etapa es un pod con la imagen bolsalab/pipeline en vez de un
comando en el computador:

    verificar_fuente -> preparar_datos -> validar_datos -> construir_variables
    -> validar_variables -> comparar_modelos -> compuerta_calidad
    -> exportar_prototipo -> [desempeno_grupos, explicacion_shap]

Todas las etapas montan el volumen bolsalab-trabajo (deploy/k8s/local/pipeline-storage.yaml)
en data/, reports/ y models/: lo que escribe una etapa lo lee la siguiente.
Las corridas van al MLflow del namespace mlops.

Nunca corre train.py --final: la medición única en la prueba no está en Kubernetes.
"""

from datetime import datetime, timedelta

from airflow.providers.cncf.kubernetes.operators.pod import KubernetesPodOperator
from airflow.sdk import dag
from kubernetes.client import models as k8s

IMAGE = "bolsalab/pipeline:dev"          # cargada en kind con `kind load docker-image`
NAMESPACE = "airflow"                    # la cuenta de servicio del chart ya puede crear pods aquí
VOLUME_CLAIM = "bolsalab-trabajo"
MLFLOW_TRACKING_URI = "http://mlflow.mlops.svc.cluster.local:5000"

# Propuesta del equipo, pendiente de registrar en el protocolo.
UMBRALES = {
    "auroc_minimo": 0.60,              # por debajo, algo se rompió en los datos o en el código
    "pendiente_min": 0.8,
    "pendiente_max": 1.25,
}

# Código de salida con el que una etapa se marca como "saltada" y no como "fallida".
SKIP = 99

VOLUME = k8s.V1Volume(
    name="trabajo",
    persistent_volume_claim=k8s.V1PersistentVolumeClaimVolumeSource(claim_name=VOLUME_CLAIM),
)
MOUNTS = [
    k8s.V1VolumeMount(name="trabajo", mount_path=f"/app/{folder}", sub_path=folder)
    for folder in ("data", "reports", "models")
]


def etapa(task_id: str, command: str, memoria: str = "2Gi", **kwargs) -> KubernetesPodOperator:
    """Una etapa del flujo: un pod que corre `command` dentro de /app."""
    return KubernetesPodOperator(
        task_id=task_id,
        name=f"bolsalab-{task_id.replace('_', '-')}",
        namespace=NAMESPACE,
        image=IMAGE,
        image_pull_policy="IfNotPresent",   # en kind la imagen ya está en los nodos
        cmds=["bash", "-c"],
        arguments=[command],
        env_vars={"MLFLOW_TRACKING_URI": MLFLOW_TRACKING_URI},
        volumes=[VOLUME],
        volume_mounts=MOUNTS,
        container_resources=k8s.V1ResourceRequirements(
            requests={"cpu": "500m", "memory": "512Mi"},
            limits={"memory": memoria},       # si se pasa, el pod muere con OOMKilled
        ),
        get_logs=True,                        # el log del pod aparece en la interfaz de Airflow
        on_finish_action="delete_succeeded_pod",  # los que fallan quedan para revisarlos
        **kwargs,
    )


# Revisa si el modelo de models/ ya fue medido en la prueba. Sale con 99 si es así.
GUARD_FINAL_MODEL = (
    "python -c \"import json, sys; "
    "from bolsalab.config import MODELS_DIR, MODEL_ARTIFACT_NAME; "
    "p = MODELS_DIR / f'{MODEL_ARTIFACT_NAME}.json'; "
    "sys.exit(99 if p.exists() and json.loads(p.read_text()).get('test') else 0)\""
)

# Reglas de calidad sobre reports/benchmark.csv. Corre en la imagen del proyecto.
COMPUERTA = f'''
import pandas as pd
from bolsalab.modeling.train import BENCHMARK_FILE, MODELS, choose_winner

u = {UMBRALES!r}
benchmark = pd.read_csv(BENCHMARK_FILE)
faltan = set(MODELS) - set(benchmark["model"])
if faltan:
    raise SystemExit(f"benchmark.csv no tiene estos modelos: {{sorted(faltan)}}")
if benchmark[["auroc", "auroc_sd", "calibration_slope"]].isna().any().any():
    raise SystemExit("benchmark.csv tiene métricas vacías")

fila = benchmark.set_index("model")
ganador = choose_winner(benchmark)
auroc = fila.loc[ganador, "auroc"]
pendiente = fila.loc[ganador, "calibration_slope"]

problemas = []
if auroc < u["auroc_minimo"]:
    problemas.append(f"AUROC {{auroc:.3f}} < {{u['auroc_minimo']}}")
if ganador != "logistic" and auroc <= fila.loc["logistic", "auroc"]:
    problemas.append("el ganador no supera a la regresión logística")
if not u["pendiente_min"] <= pendiente <= u["pendiente_max"]:
    problemas.append(f"pendiente de calibración {{pendiente:.2f}} fuera de rango")
if problemas:
    raise SystemExit(f"No pasa la compuerta ({{ganador}}): " + "; ".join(problemas))

print(f"Pasa la compuerta: {{ganador}} con AUROC {{auroc:.3f}} y pendiente {{pendiente:.2f}}")
'''


@dag(
    dag_id="bolsalab_entrenamiento_k8s",
    description="De la encuesta japonesa al modelo de la app, cada etapa en su pod",
    schedule=None,          # a mano o cuando haya datos nuevos; los datos de 2020 no cambian solos
    start_date=datetime(2026, 11, 1),
    catchup=False,
    default_args={"owner": "grupo-10", "retries": 0, "execution_timeout": timedelta(hours=2)},
    tags=["bolsalab", "entrenamiento", "kubernetes"],
)
def bolsalab_entrenamiento_k8s():

    # 1. La encuesta tiene que estar en el volumen: si falta, las pruebas de datos
    #    se saltarían en silencio. También reports/tuning.csv, el resultado del ajuste
    #    que eligió FINAL_MODEL: exportar_prototipo lo lee y ninguna etapa lo produce.
    verificar_fuente = etapa(
        "verificar_fuente",
        "python -c \"from bolsalab.config import JAPAN_SURVEY_FILE as f; "
        "from bolsalab.modeling.tuning import TUNING_FILE as t; "
        "assert f.exists(), f'Falta la encuesta: {f}'; "
        "assert t.exists(), f'Falta el resultado del ajuste: {t}'\"",
        memoria="512Mi",
    )

    # 2-3. Carga y limpieza, y los valores del protocolo (sección 2).
    preparar_datos = etapa("preparar_datos", "python -m bolsalab.dataset", memoria="3Gi")
    validar_datos = etapa("validar_datos", "pytest -q tests/test_dataset.py", memoria="3Gi")

    # 4-5. Las 17 variables y `sold`.
    construir_variables = etapa("construir_variables", "python -m bolsalab.features")
    validar_variables = etapa("validar_variables", "pytest -q tests/test_features.py",
                              memoria="3Gi")

    # 6. Los 7 modelos con validación anidada 5 x 3. No toca la prueba. La etapa más pesada.
    comparar_modelos = etapa("comparar_modelos", "python -m bolsalab.modeling.train",
                             memoria="4Gi")

    # 7. Reglas de calidad sobre reports/benchmark.csv.
    compuerta_calidad = etapa("compuerta_calidad", f"python - <<'EOF'\n{COMPUERTA}\nEOF",
                              memoria="1Gi")

    # 8. Exporta para la app y registra en MLflow, salvo que models/ ya tenga el modelo final.
    exportar_prototipo = etapa(
        "exportar_prototipo",
        f"{GUARD_FINAL_MODEL} && python -m bolsalab.modeling.train --prototype",
        skip_on_exit_code=SKIP,
    )

    # 9-10. Revisiones del modelo que quedó en models/ (corren aunque la exportación se salte).
    desempeno_grupos = etapa("desempeno_grupos", "python -m bolsalab.modeling.groups",
                             trigger_rule="none_failed")
    explicacion_shap = etapa("explicacion_shap", "python -m bolsalab.explain",
                             memoria="3Gi", trigger_rule="none_failed")

    (
        verificar_fuente
        >> preparar_datos >> validar_datos
        >> construir_variables >> validar_variables
        >> comparar_modelos >> compuerta_calidad
        >> exportar_prototipo >> [desempeno_grupos, explicacion_shap]
    )


bolsalab_entrenamiento_k8s()
