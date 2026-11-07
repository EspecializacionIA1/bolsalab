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

### Red neuronal (8 experimentos más, 3 de noviembre de 2026)

Dilan sumó la red neuronal a la exploración, con una rejilla ampliada de 4 tamaños de red, 3 niveles de regularización y 2 velocidades de aprendizaje. Con esto son 32 experimentos.

- **Ajustar más sí ayudó a la red.** Pasó de 0,635 a 0,650 y se volvió más estable: la desviación bajó de 0,018 a 0,003.
- **Sigue por debajo.** Su mejor resultado (0,650) apenas supera a la regresión logística (0,646) y queda lejos del umbral de reemplazo.
- **Exagera las probabilidades.** Su pendiente de calibración queda entre 0,80 y 0,94, siempre por debajo de 1.

## 3. Ajuste por familias

Responde a la retroalimentación de tutoria: ajustar cada familia según cómo aprende, no con rejillas más grandes. El plan está en `docs/plan-ajuste-por-familias.md`, las reglas en el protocolo (sección 7) y el código en `bolsalab/modeling/tuning.py`. Los resultados se guardan en `reports/tuning.csv`. Desde aquí medimos también la brecha de sobreajuste: el AUROC con las personas que el modelo vio, menos el AUROC con personas nuevas.

### Paso 1. Parada temprana (5 de noviembre de 2026)

Antes, los tres modelos de boosting usaban 300 árboles fijos. Ahora cada modelo agrega árboles mientras mejore en un 10 % apartado de sus datos de entrenamiento, con un máximo de 2.000, y se detiene tras 50 árboles sin mejorar.

| Modelo | AUROC con 300 fijos | AUROC con parada temprana | Pendiente antes → ahora | Brecha | Árboles elegidos |
|---|---|---|---|---|---|
| XGBoost | 0,6601 | 0,6594 ± 0,003 | 1,056 → 0,988 | 0,022 | 108 a 557 |
| LightGBM | 0,6600 | 0,6595 ± 0,003 | 1,055 → 0,999 | 0,021 | 111 a 450 |
| CatBoost | 0,6613 | 0,6612 ± 0,004 | 1,096 → 1,063 | 0,021 | 224 a 491 |

- **El número de árboles no era el límite.** El AUROC cambió menos que la variación entre particiones. Ninguno pasa de 0,6636, así que XGBoost sigue como ganador.
- **La calibración mejoró.** Con velocidad 0,03 el modelo necesitaba de 450 a 550 árboles; con 300 no terminaba de aprender y sus probabilidades quedaban apretadas hacia el promedio. Con velocidad 0,1 le bastaban de 110 a 130, y los 300 sobraban.
- **No hay sobreajuste.** Las tres brechas quedan entre 0,021 y 0,022, por debajo del límite de 0,03.
- **El tope de 2.000 no influyó.** El máximo elegido fue 557.
- **Siguen pidiendo ser simples.** Las 15 particiones de XGBoost y LightGBM eligieron profundidad 3, y CatBoost eligió profundidad 4 en 4 de 5.

### Paso 2. Poda de cada árbol (5 de noviembre de 2026)

Sobre la parada temprana del paso 1, con la profundidad fija en 3, probamos `gamma` (XGBoost) o `min_split_gain` (LightGBM), que exigen que cada corte mejore al menos ese valor, y `reg_lambda`, que acerca al promedio las hojas con riesgos extremos.

| Modelo | AUROC | Pendiente | Brecha | Lo que eligieron las 5 particiones |
|---|---|---|---|---|
| XGBoost | 0,6595 ± 0,004 | 1,010 | 0,019 | `reg_lambda` 10 en las 5; `gamma` entre 0 y 1, sin patrón |
| LightGBM | 0,6601 ± 0,003 | 1,005 | 0,019 | `reg_lambda` 5 o 10; `min_split_gain` 0 o 0,5 |

- **La poda no sube el AUROC.** Cambia menos de 0,001 frente al paso 1, y ninguno pasa de 0,6636.
- **Baja un poco el sobreajuste.** La brecha pasa de 0,022 a 0,019, con la calibración cerca de 1.
- **Lo que pesa es `reg_lambda`, no `gamma`.** XGBoost eligió el valor más alto (10) en las 5 particiones, y `gamma` no mostró un patrón. Como la poda no mejoró más que la variación entre particiones, no ampliamos esta rejilla (regla del plan).
- **Conclusión:** la profundidad 3 ya controlaba bien el árbol; la poda lo confirma.

## Lo que sigue

- Pasos 3 a 6 del plan de ajuste por familias.
- Congelar el modelo y medirlo una sola vez en el 20 % de prueba (`uv run python -m bolsalab.modeling.train --final`) y en la NFCS.
