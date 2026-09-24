"""Etapa 3 del pipeline: feature engineering y construcción de los datasets.

Produce los dos datasets de entrenamiento en data/processed:

- dataset_perfil.parquet: una fila por persona. Features: respuestas del
  cuestionario, capacidad económica, horizonte y conocimiento. Etiqueta:
  arquetipo (ver config.ARQUETIPOS). Base sintética calibrada con SCF e IEFIC.
- dataset_mercado.parquet: una fila por clase de activo y día hábil BVC.
  Features: retornos, volatilidad, drawdown, macro colombiana y variables globales.

Uso: python -m bolsalab.features
"""


def construir_dataset_perfil() -> None:
    raise NotImplementedError


def construir_dataset_mercado() -> None:
    raise NotImplementedError


def main() -> None:
    construir_dataset_perfil()
    construir_dataset_mercado()


if __name__ == "__main__":
    main()
