# BolsaLAB

Copiloto educativo de inversión para principiantes en Colombia. Proyecto de la Especialización en IA, Pontificia Universidad Javeriana (Grupo 10).

BolsaLAB estima **qué tan propensa es una persona a vender sus inversiones durante una caída del mercado**. Lo hace con un modelo entrenado desde cero sobre una encuesta real a 54.704 inversionistas japoneses que vivieron la caída de marzo de 2020.

> Prototipo académico. No constituye asesoría de inversión y nunca recomienda comprar o vender un activo.

## Qué hace la app

1. **Pregunta.** La persona responde unas 14 preguntas: edad, educación, situación familiar, ingreso, tres preguntas de conocimiento financiero y cómo se ve a sí misma frente al riesgo. Cada pregunta corresponde a una columna del dataset de entrenamiento.
2. **Consulta el modelo.** El frontend envía las respuestas a la API, que llama al modelo y devuelve el resultado.
3. **Muestra el resultado.** La persona ve si es más, igual o menos propensa a vender que el promedio, y las respuestas que más pesaron. La app no muestra un porcentaje personal: el modelo se entrenó en Japón y ese número no sería confiable en Colombia.

## El modelo

| | |
|---|---|
| Datos de entrenamiento | Encuesta de Bawalle, Khan y Kadoya (2025), PLOS ONE: clientes de un corredor en línea de Japón |
| Población | Personas que en marzo de 2020 vendieron todo, vendieron parte o mantuvieron sus inversiones (54.704) |
| Variable objetivo | `sold`: 1 si vendió todo o parte (19,87 %), 0 si mantuvo |
| Modelos que comparamos | Trivial, regresión logística, Random Forest, XGBoost, LightGBM, CatBoost y una red neuronal pequeña |
| Contraste fuera de Japón | Panel de la Survey of Consumer Finances 2007-2009 (Reserva Federal de EE. UU.) |

Las reglas para preparar los datos, partirlos, medir y elegir el modelo están en [`docs/protocolo-evaluacion.md`](docs/protocolo-evaluacion.md). Cada regla cita el artículo que la respalda. Las variables que usa el modelo, y las que no, están en [`docs/variables.md`](docs/variables.md).

## Prototipo en Streamlit

`app/app.py` es la app del prototipo: cuestionario, resultado explicado con SHAP y qué aprender. Cómo correrla, las decisiones y lo que encontramos con SHAP están en [`docs/prototipo.md`](docs/prototipo.md).

```bash
uv sync --group app
uv run --group app streamlit run app/app.py
```

## La API

El backend expone un endpoint. Los nombres de la ruta y de los campos son una propuesta del equipo.

```
POST /api/v1/crash-reaction/predict
```

Recibe las respuestas del cuestionario:

```json
{
  "age": 27,
  "gender": "female",
  "university": false,
  "married": false,
  "has_children": false,
  "urban": true,
  "employed": true,
  "income_bracket": 3,
  "assets_bracket": 1,
  "knowledge": { "interest": "correct", "inflation": "dont_know", "diversification": "correct" },
  "knowledge_confidence": 4,
  "risk_aversion": 3,
  "short_term_view": 4
}
```

Devuelve la categoría y lo que la explica:

```json
{
  "model_version": "crash_reaction_v1",
  "probability": 0.231,
  "base_rate": 0.1987,
  "relative_to_average": 1.16,
  "category": "similar",
  "top_factors": [
    { "feature": "financial_literacy", "direction": "increases", "label": "Acertó 2 de 3 preguntas de conocimiento" }
  ],
  "in_training_range": true,
  "warnings": ["assets_at_lowest_training_bracket"]
}
```

`probability` es de uso interno; la pantalla muestra `category` (`more_likely`, `similar` o `less_likely`), los factores y los avisos.

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
├── notebooks/             ← Exploración y análisis
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
- **Notebooks:** se nombran `<orden>-<iniciales>-<descripcion>.ipynb`, por ejemplo `3.0-jga-comparacion-modelos.ipynb`. El código que se reutiliza pasa a `bolsalab/`.
- **Datos:** no se suben a git. Los de la NFCS tampoco se comparten entre integrantes: sus términos lo prohíben.
- **Parámetros:** rutas y semillas se leen de `bolsalab/config.py`.

## Si el tiempo alcanza

- **Ruta de aprendizaje:** módulos cortos según las respuestas que más pesaron en el resultado.
- **Simulador de caída:** vivir la caída con una cartera de ejemplo y registrar qué decide la persona.
- **Librerías:** `optuna` (búsqueda de hiperparámetros) y `riskfolio-lib` (carteras de ejemplo) se pueden agregar si se llegan a necesitar.
