# BolsaLAB

Copiloto educativo de inversión para principiantes en Colombia. Proyecto de la Especialización en IA, Pontificia Universidad Javeriana (Grupo 10).

BolsaLAB estima **qué tan propensa es una persona a vender sus inversiones durante una caída del mercado**. Lo hace con un modelo entrenado desde cero sobre una encuesta real a 54.704 inversionistas japoneses que vivieron la caída de marzo de 2020.

> Prototipo académico. No constituye asesoría de inversión y nunca recomienda comprar o vender un activo.

## Qué hace la app

1. **Pregunta.** La persona responde 13 preguntas: edad, sexo, educación, situación familiar, empleo, ingreso, ahorros, tres preguntas de conocimiento financiero y qué tan segura se siente de lo que sabe. Cada pregunta corresponde a una columna del dataset de entrenamiento.
2. **Consulta el modelo.** Las respuestas pasan al modelo congelado, que devuelve el resultado.
3. **Muestra el resultado.** La persona ve si es más, igual o menos propensa a vender que el promedio, y las respuestas que más pesaron. La app no muestra un porcentaje personal: el modelo se entrenó en Japón y ese número no sería confiable en Colombia.

## El modelo

| | |
|---|---|
| Datos de entrenamiento | Encuesta de Bawalle, Khan y Kadoya (2025), PLOS ONE: clientes de un corredor en línea de Japón |
| Población | Personas que en marzo de 2020 vendieron todo, vendieron parte o mantuvieron sus inversiones (54.704) |
| Variable objetivo | `sold`: 1 si vendió todo o parte (19,87 %), 0 si mantuvo |
| Modelos que comparamos | Trivial, regresión logística, Random Forest, XGBoost, LightGBM, CatBoost y una red neuronal pequeña |
| Contraste fuera de Japón | Preparamos la tabla del panel de la Survey of Consumer Finances 2007-2009 (Reserva Federal de EE. UU.), pero el modelo no se evaluó ahí |
| Modelo final | XGBoost con parada temprana y poda, con 17 variables |
| Resultado en la prueba final | AUROC 0,670 (0,658 a 0,682) con 10.941 personas que el modelo nunca vio. En el 10 % de mayor riesgo vendió el 40,8 %, el doble del promedio |

Las reglas para preparar los datos, partirlos, medir y elegir el modelo están en [`docs/protocolo-evaluacion.md`](docs/protocolo-evaluacion.md). Cada regla cita el artículo que la respalda. Las variables que usa el modelo, y las que no, están en [`docs/variables.md`](docs/variables.md). El detalle de la prueba final está en [`docs/experimentos.md`](docs/experimentos.md), sección 4.

Todo el recorrido queda en MLflow. Para verlo en tu computador:

```bash
uv run python -m bolsalab.modeling.mlflow_backfill   # carga las pruebas de la comparación y del ajuste
uv run python -m bolsalab.modeling.mlflow_tracking   # registra el modelo final que está en models/
uv run mlflow ui --backend-store-uri sqlite:///mlflow.db
```

## Prototipo en Streamlit

`app/app.py` es la app del prototipo: cuestionario, resultado explicado con SHAP y qué aprender. Cómo correrla, las decisiones y lo que encontramos con SHAP están en [`docs/prototipo.md`](docs/prototipo.md).

```bash
uv sync --group app
uv run --group app streamlit run app/app.py
```

## La API

La API usa `bolsalab/modeling/predict.py`, el mismo código de la app de Streamlit. La ruta es una propuesta del equipo:

```
POST /api/v1/crash-reaction/predict
```

Recibe las respuestas del cuestionario. Los niveles van de 1 a 5 frente a la gente del país, y la confianza de 1 a 5:

```json
{
  "age": 27,
  "male": false,
  "university": true,
  "married": false,
  "has_children": false,
  "urban": true,
  "employed": true,
  "income_level": 3,
  "assets_level": 1,
  "interest": "more",
  "inflation": "dont_know",
  "diversification": "false",
  "knowledge_confidence": 4
}
```

Devuelve la categoría y lo que la explica:

```json
{
  "model_version": "crash_reaction_v1",
  "category": "similar",
  "top_factors": [
    { "feature": "knows_inflation", "label": "...", "direction": "increases", "impact": 0.21, "actionable": true }
  ],
  "failed_questions": ["inflation"],
  "overconfident": false,
  "not_asked": ["risk_aversion", "short_term_view"],
  "warnings": []
}
```

`predict()` también devuelve `probability` y `base_rate`, que son de uso interno. La pantalla muestra `category` (`more_likely`, `similar` o `less_likely`), los factores y los avisos. Nunca muestra la probabilidad.

## Cómo está organizado el repositorio

Seguimos la plantilla [Cookiecutter Data Science v2](https://cookiecutter-data-science.drivendata.org/): separa los datos del código y la exploración de la producción.

```
bolsalab/
├── bolsalab/              ← Paquete Python con el pipeline de ML
│   ├── config.py          ← Rutas y semilla. Todo parámetro sale de aquí
│   ├── dataset.py         ← Carga y limpieza del dataset de Japón
│   ├── features.py        ← Variables de entrada y variable objetivo
│   ├── explain.py         ← Explicación global del modelo con SHAP
│   ├── modeling/
│   │   ├── train.py       ← Entrenar, comparar y exportar el modelo
│   │   └── predict.py     ← Cargar el modelo publicado y predecir
│   └── plots.py           ← Gráficas reutilizables
├── data/                  ← NO se versiona
│   ├── external/crash/    ← Datasets descargados a mano (Japón, panel SCF y otros)
│   ├── interim/           ← Tablas limpias
│   └── processed/         ← Datasets finales para entrenar
├── docs/                  ← Protocolo de evaluación, comandos de uv y entregables
├── models/                ← Modelos publicados (.joblib) y su metadata
├── notebooks/             ← Resultados para el tutor, en orden (00, 01, ...)
│   ├── 1_datos/           ← Exploración de los datos y comparación con la NFCS
│   ├── 2_modelado/        ← Comparación de modelos, modelado paso a paso y SHAP
│   └── 3_mejora_auroc/    ← Ajuste por familias, variables y ruta para mejorar el AUROC
├── reports/figures/       ← Gráficas para entregas y sustentación
├── tests/                 ← Pruebas del paquete
├── app/                   ← Prototipo en Streamlit
├── backend/               ← API en FastAPI que expone el modelo
└── frontend/prototypes/   ← Prototipos HTML validados con usuarios
```

## Cómo fluye el trabajo

```
data/external ──► data/interim ──► data/processed ──► models/ ──► backend/ ──► frontend/
  dataset de        limpieza         variables y        modelo      API         app
  Japón                              objetivo           elegido     FastAPI
```

## Primeros pasos

```bash
git clone git@github.com:EspecializacionIA1/bolsalab.git
cd bolsalab
uv sync
cp .env.example .env
```

Los datos no se versionan. Cada integrante los descarga de su fuente y los guarda en `data/external/crash/`. En [`docs/datos.md`](docs/datos.md) está para qué usamos cada dataset, de dónde se baja y qué permiten sus términos. Los dos principales:

- **Japón:** archivo S1 del artículo de Bawalle, Khan y Kadoya (2025) en PLOS ONE, https://doi.org/10.1371/journal.pone.0315622
- **Panel SCF 2007-2009:** Reserva Federal de EE. UU., https://www.federalreserve.gov/econres/scf_2009p.htm

Los comandos de uso diario están en [`docs/uv-commands.md`](docs/uv-commands.md).

## Convenciones del equipo

- **Ramas:** nadie hace push directo a `main`. Cada tarea va en `feature/<descripcion>` y entra por Pull Request con al menos una aprobación.
- **Notebooks:** van en la subcarpeta de su tema y se nombran `<orden> - <descripción>.ipynb`, con un número que sigue el orden del proyecto, por ejemplo `2_modelado/02 - Comparación de modelos.ipynb`. Un notebook nuevo toma el siguiente número libre. El código que se reutiliza pasa a `bolsalab/`.
- **Datos:** no se suben a git. Los de la NFCS tampoco se comparten entre integrantes: sus términos lo prohíben.
- **Parámetros:** rutas y semillas se leen de `bolsalab/config.py`.

## Si el tiempo alcanza

- **Ruta de aprendizaje:** módulos cortos según las respuestas que más pesaron en el resultado.
- **Simulador de caída:** vivir la caída con una cartera de ejemplo y registrar qué decide la persona.
- **Librerías:** `optuna` (búsqueda de hiperparámetros) y `riskfolio-lib` (carteras de ejemplo) se pueden agregar si se llegan a necesitar.
