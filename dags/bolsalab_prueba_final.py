"""Flujo 2 de BolsaLAB: la medición única en el 20 % de prueba.

Solo a mano. Falla si nadie confirmó la medición o si el modelo de models/ ya
fue medido en la prueba (protocolo, sección 7: la prueba se mira una sola vez).
"""

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import Param, dag

from bolsalab_comun import DEFAULT_ARGS, ENV, GUARD_FINAL_MODEL, REPO, RUN, START_DATE, UV


def bash(task_id, command, **kwargs):
    return BashOperator(task_id=task_id, bash_command=command, env=ENV, append_env=True,
                        **kwargs)


@dag(
    dag_id="bolsalab_prueba_final",
    description="Medición única del ganador en el 20 % de prueba (solo a mano)",
    schedule=None,
    start_date=START_DATE,
    catchup=False,
    default_args=DEFAULT_ARGS,
    max_active_runs=1,
    params={
        "confirmo_prueba_unica": Param(
            False, type="boolean",
            description="Marcar solo si el equipo acordó medir en la prueba y nunca se ha hecho",
        ),
    },
    tags=["bolsalab", "prueba-final"],
)
def bolsalab_prueba_final():

    # Candado 1: alguien confirmó. Candado 2: la prueba no se ha usado.
    # El guardián sale con 99 si ya se usó; aquí eso cuenta como falla, no como salto.
    confirmar_prueba_unica = bash(
        "confirmar_prueba_unica",
        '[ "{{ params.confirmo_prueba_unica }}" = "True" ] '
        '|| { echo "Falta confirmar confirmo_prueba_unica al disparar el flujo"; exit 1; }; '
        f'cd "{REPO}" && {UV} run python -c "{GUARD_FINAL_MODEL}" '
        '|| { echo "El modelo de models/ ya fue medido en la prueba. No se repite."; exit 1; }',
        skip_on_exit_code=None,
    )

    # Entrena al ganador, lo mide en la prueba, lo guarda en models/ y lo registra en MLflow.
    medir_en_prueba = bash("medir_en_prueba", RUN + "bolsalab.modeling.train --final")

    desempeno_grupos = bash("desempeno_grupos", RUN + "bolsalab.modeling.groups")

    confirmar_prueba_unica >> medir_en_prueba >> desempeno_grupos


bolsalab_prueba_final()
