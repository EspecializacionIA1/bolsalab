# Atajos del pipeline. En Windows sin `make`, ejecutar el comando de la derecha directamente.

.PHONY: install data features train test

install:   ## Crea el entorno con las versiones exactas de uv.lock
	uv sync

data:      ## Etapa 1: descarga de fuentes automáticas -> data/raw
	uv run python -m bolsalab.dataset

features:  ## Etapa 3: construye los datasets de entrenamiento -> data/processed
	uv run python -m bolsalab.features

train:     ## Etapas 4-5: compara modelos, elige y exporta el artefacto -> models/
	uv run python -m bolsalab.modeling.train

test:
	uv run pytest tests
