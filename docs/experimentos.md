# Comparación de modelos y experimentos

Código en `bolsalab/modeling/train.py` y `bolsalab/modeling/experiments.py`. Resultados en `reports/benchmark.csv` y `reports/experiments.csv`. Las reglas están en `docs/protocolo-evaluacion.md`, secciones 4 a 7. Los resultados con gráficas están en `notebooks/Comparación de modelos.ipynb`.

Todo se midió con el 80 % de entrenamiento de Japón (43.763 personas), con validación cruzada anidada 5 × 3. El 20 % de prueba no se ha tocado.

## 1. Comparación de los 7 modelos

| Modelo | AUROC |
|---|---|
| Trivial | 0,500 |
| Regresión logística | 0,646 |
| Random Forest | 0,657 |
| **XGBoost** | **0,660 ± 0,004** |
| LightGBM | 0,660 |
| CatBoost | 0,661 |
| Red neuronal | 0,635 |

Por la regla del protocolo gana **XGBoost**: CatBoost sacó 0,661, pero la diferencia es menor que una desviación, y entre modelos casi iguales elegimos el más simple de la lista.

## 2. Experimentos

Probamos XGBoost, LightGBM y CatBoost con dos rejillas de ajustes (la del protocolo y una ampliada que propuso Dilan) y cuatro versiones de las variables: sin cambios, sin edad al cuadrado, con logaritmo del ingreso y con edad por ingreso. Son 24 experimentos. Las rejillas y la regla para reemplazar al ganador quedaron en el protocolo antes de correrlos.

**Resultado: XGBoost sigue siendo el ganador.** Para reemplazarlo había que pasar de 0,6636 (su AUROC más una desviación). El mejor experimento llegó a 0,6613.

Lo que encontramos:

- **Ajustar más no mejora.** Los 24 quedaron entre 0,659 y 0,661, una diferencia menor que la variación entre repeticiones. El límite está en la información del cuestionario, no en el modelo. Concuerda con Bawalle et al. (2025), que reportan un pseudo R² menor de 0,04.
- **Las transformaciones no cambian nada en los árboles.** Sin edad al cuadrado o con logaritmo del ingreso, el resultado es idéntico: los árboles cortan por "mayor o menor que" y esas transformaciones no cambian el orden de las personas. Multiplicar edad por ingreso empeora un poco.
- **Los ajustes elegidos son estables.** En XGBoost y LightGBM las 5 repeticiones eligieron los mismos ajustes, así que el resultado no depende del reparto de personas. CatBoost dudó entre profundidad 4 y 6.
- **Los modelos piden ser simples.** Todos eligieron la profundidad más baja disponible (3) y, en la rejilla ampliada, las opciones más conservadoras (hojas con más personas, menos hojas). No vale la pena buscar configuraciones más complejas.
- **Calibración.** La pendiente ideal es 1. XGBoost queda en 1,06 con la rejilla del protocolo y en 1,04 con la ampliada; CatBoost, entre 1,08 y 1,11. Todas pasan de 1: las probabilidades salen algo apretadas hacia el promedio. La regla de reemplazo solo mira el AUROC, así que esto no cambia al ganador.

## Lo que sigue

- Medir a XGBoost una sola vez en el 20 % de prueba (`uv run python -m bolsalab.modeling.train --final`).
- Explicar sus predicciones con SHAP.
- Probarlo en EE. UU. con la NFCS.
