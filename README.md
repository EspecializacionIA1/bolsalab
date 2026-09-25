# BolsaLAB

Copiloto educativo de inversión con IA explicable para inversionistas principiantes en Colombia. Proyecto de la Especialización en IA, Pontificia Universidad Javeriana (Grupo 10).

BolsaLAB construye un portafolio según el perfil de riesgo real de la persona y le muestra **primero cuánto puede perder** antes de decirle cuánto podría ganar.

- **Pérdidas primero:** la peor caída histórica, en pesos, antes que cualquier rentabilidad.
- **Español claro:** cada decisión se explica sin jerga financiera.
- **Simulador de caída:** la persona vive una crisis real y se compara lo que hace con lo que dijo que haría.
- **Nunca recomienda activos:** cuando la pregunta es de asesoría regulada, remite a una firma vigilada por la Superintendencia Financiera.

> Prototipo académico. No constituye asesoría de inversión.

## Cómo está organizado el repositorio

La estructura sigue la plantilla estándar [Cookiecutter Data Science v2](https://cookiecutter-data-science.drivendata.org/). La elegimos porque:

- **Separa los datos del código.** Los datos se regeneran con el pipeline y nunca se suben a git.
- **Separa la exploración de la producción.** Los notebooks sirven para explorar y documentar. El código reutilizable vive en el paquete `bolsalab/`, que es lo que importa el backend.
- **Cualquiera se ubica rápido.** Es la convención más usada en proyectos de ML en Python.

```
bolsalab/
├── bolsalab/              ← Paquete Python con el pipeline de ML (lo que importa el backend)
│   ├── config.py          ← Rutas, activos, fuentes y semillas. Todo parámetro sale de aquí
│   ├── dataset.py         ← Etapas 1-2: descarga y limpieza de datos
│   ├── features.py        ← Etapa 3: feature engineering y datasets de entrenamiento
│   ├── modeling/
│   │   ├── train.py       ← Etapas 4-5: comparar modelos, elegir y exportar
│   │   └── predict.py     ← Cargar el modelo publicado y predecir
│   └── plots.py           ← Gráficas reutilizables
├── data/                  ← NO se versiona (ver .gitignore)
│   ├── raw/               ← Descargas automáticas, tal cual llegan de la fuente
│   ├── external/          ← Descargas manuales (COLCAP de la BVC, encuestas SCF e IEFIC)
│   ├── interim/           ← Una tabla limpia por fuente
│   └── processed/         ← Datasets finales para entrenar
├── models/                ← Modelos publicados (.joblib) + su metadata (.json)
├── notebooks/             ← Exploración y comparación de modelos
├── docs/                  ← Documentación de uso (commands.md: comandos para copiar y pegar)
├── references/            ← Diccionario de datos, fuentes y licencias
├── reports/figures/       ← Gráficas para entregas y sustentación
├── tests/                 ← Pruebas del paquete
├── backend/               ← API en FastAPI que expone el modelo
├── frontend/              ← Aplicación web
│   └── prototypes/        ← Prototipos HTML v1 y v2 validados con usuarios (Design Thinking)
├── pyproject.toml         ← Dependencias del proyecto (equivale a package.json)
├── uv.lock                ← Versiones exactas instaladas (equivale a package-lock.json)
├── .python-version        ← Versión de Python del proyecto (3.12)
├── Makefile               ← Atajos: make data / make features / make train
└── .env.example           ← Variables de entorno necesarias (copiar a .env)
```

## Cómo fluye el trabajo

Cada carpeta corresponde a una etapa. Los datos avanzan de izquierda a derecha:

```
Fuentes ──► data/raw ──► data/interim ──► data/processed ──► models/ ──► backend/ ──► frontend/
            descarga      limpieza          features y         modelo      API          interfaz
                                            datasets           elegido     FastAPI      web
```

| Etapa | Qué se hace | Dónde |
|---|---|---|
| 1. Obtención | Descargar precios, macro y encuestas | `bolsalab/dataset.py` → `data/raw`, `data/external` |
| 2. Limpieza | Festivos, tickers renombrados, calendario BVC, fechas de publicación | `bolsalab/dataset.py` → `data/interim` |
| 3. Features | Construir el dataset de perfil y el de mercado | `bolsalab/features.py` → `data/processed` |
| 4. Modelado | Entrenar y comparar candidatos, elegir el mejor | `notebooks/` + `bolsalab/modeling/train.py` |
| 5. Publicación | Exportar el modelo ganador a `.joblib` + metadata | `models/` |
| 6. API | Exponer el modelo con FastAPI | `backend/` |
| 7. Interfaz | Consumir la API desde la web | `frontend/` |

## Primeros pasos

El proyecto usa [uv](https://docs.astral.sh/uv/) para manejar Python y las dependencias (similar a npm). Instalarlo una vez: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` en Windows, o `curl -LsSf https://astral.sh/uv/install.sh | sh` en Linux/Mac.

```bash
git clone git@github.com:EspecializacionIA1/bolsalab.git
cd bolsalab
uv sync                         # descarga Python 3.12, crea .venv e instala todo desde uv.lock
cp .env.example .env            # y completar los valores
```

**Todos los comandos para copiar y pegar** (descargar datos, revisarlos, correr pruebas, manejar dependencias) están en [`docs/commands.md`](docs/commands.md).

## Convenciones del equipo

- **Dependencias:** se agregan solo con `uv add`, nunca con `pip install`, y `uv.lock` se sube a git para que todos tengan las mismas versiones.
- **Ramas:** nadie hace push directo a `main`. Se trabaja en `feature/<descripcion>` y se integra por Pull Request con al menos una aprobación.
- **Notebooks:** se nombran `<orden>-<iniciales>-<descripcion>.ipynb`, por ejemplo `3.0-jga-comparacion-modelos.ipynb`. Si un notebook produce código que se va a reutilizar, ese código pasa a `bolsalab/`.
- **Datos:** no se suben a git. Cualquiera los regenera ejecutando el pipeline. Las descargas manuales se documentan en `references/`.
- **Parámetros:** rutas, tickers y fechas se leen de `bolsalab/config.py`, nunca se escriben a mano en un notebook.
