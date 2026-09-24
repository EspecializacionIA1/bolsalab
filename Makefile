# Atajos del pipeline. En Windows sin `make`, ejecutar el comando de la derecha directamente.

.PHONY: install data features train test

install:   ## Crea el entorno de desarrollo
	pip install -r requirements.txt

data:      ## Etapas 1-2: descarga y limpieza  -> data/raw, data/interim
	python -m bolsalab.dataset

features:  ## Etapa 3: construye los datasets de entrenamiento -> data/processed
	python -m bolsalab.features

train:     ## Etapas 4-5: compara modelos, elige y exporta el artefacto -> models/
	python -m bolsalab.modeling.train

test:
	pytest tests
