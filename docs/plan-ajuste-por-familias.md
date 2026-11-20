# Plan de ajuste por familias de modelos

BolsaLAB · Grupo 10 

## Por qué este plan

Se nos pidió ajustar cada familia de modelos según cómo aprende, y no probando rejillas cada vez más grandes "a la fuerza". También nos pidió probar redes en PyTorch e intentar mejorar el AUROC de 0,660 de XGBoost sin sobreajustar.

Hasta ahora corrimos 32 experimentos y ninguno superó a XGBoost. Con este plan cambiamos la forma de trabajar: cada prueba tiene una razón, y su resultado decide la siguiente.

## Reglas

- **Las mismas de siempre.** Usamos el 80 % de entrenamiento, la validación anidada 5 × 3 y la semilla 42. El 20 % de prueba no se toca.
- **Medimos también el sobreajuste.** La brecha es el AUROC con las personas que el modelo vio menos el AUROC con personas nuevas. Si crece, el modelo está memorizando.
- **Reemplazar a XGBoost** exige pasar de un AUROC de **0,6636** con una brecha de **0,03** o menos.
- **Seguir o pasar al siguiente paso.** Si una prueba mejora menos de 0,004, que es lo que varía el AUROC entre particiones, la anotamos y pasamos al siguiente paso, sin ampliar su rejilla.
- **Registro previo.** Cada decisión queda en el protocolo (sección 7) antes de correr.

## Dónde vamos

| Paso | Qué probamos | Por qué | Resultado |
|---|---|---|---|
| 1 | **Parada temprana** en XGBoost, LightGBM y CatBoost: el modelo agrega árboles hasta que deja de mejorar | Antes usaban 300 árboles fijos, sin razón | El AUROC no cambió (0,659). La calibración mejoró: la pendiente pasó de 1,06 a 0,99. Brecha de 0,022 |
| 2 | **Poda**: `gamma` exige que cada corte valga la pena y `reg_lambda` castiga las hojas con riesgos extremos | Los modelos siempre eligen la profundidad mínima, señal de mucho ruido | El AUROC no cambió (0,660). La brecha bajó a 0,019. Lo que pesó fue `reg_lambda` |
| 3 | **Restricciones monótonas**: acertar las preguntas de finanzas nunca puede subir el riesgo | SHAP y Bawalle et al. (2025) muestran esa dirección, y la app enseña eso | No se hizo: con el visto bueno de nuestro tutor cerramos las pruebas el 18 de noviembre, porque el límite está en la información y no en el modelo |
| 4 | **Random Forest con poda**: `ccp_alpha` corta las ramas que aportan poco y `max_features` limita cuántas variables mira cada corte | Es la poda clásica que mencionó el tutor | No se hizo: con el visto bueno nuestro tutor cerramos las pruebas el 18 de noviembre, porque el límite está en la información y no en el modelo |
| 5 | **Variables** (ver abajo) | Una variable nueva solo ayuda si trae información que el modelo no tenía | Ninguna variable nueva mejoró (todas a menos de 0,001). Quitar las dos preguntas que la app no hace cuesta 0,0075: se quedan. El modelo conserva las 17 variables |
| 6 | **Redes en PyTorch** (ver abajo) | Lo pidió el tutor | Hecho. La mejor red sacó 0,6537 ± 0,0036 con validación anidada, por debajo del modelo final. Detalle en `docs/experimentos.md` |
| 7 | **Cierre**: congelar el modelo y medirlo una sola vez en el 20 % de prueba, con las reglas del protocolo (sección 7). La NFCS no la usamos para validar porque tiene muy pocos casos (documento del Ciclo 3B, sección 3) | | Hecho el 19 de noviembre: AUROC 0,670 (0,658 a 0,682), consistente con la validación. Modelo congelado |
| 8 | **Búsqueda con Optuna** en XGBoost: busca en rangos completos en vez de listas cortas (se corre antes del cierre; el 8 es solo el siguiente número libre) | Queremos descartar que una combinación mejor se nos esté escapando entre los valores de la rejilla | El AUROC no cambió (0,6595). Brecha de 0,016. Cada partición eligió valores distintos: no hay una combinación mejor que las demás |
| 9 | **Ideas de la literatura**: aleatoriedad en XGBoost (`subsample`, `colsample_bytree`, `min_child_weight`) y promedio de XGBoost, CatBoost y regresión logística | Son las dos ideas de los benchmarks recientes que no habíamos probado; las dos buscan no aumentar el sobreajuste | Ninguna pasó 0,6636. Aleatoriedad 0,6611 (brecha 0,022) y promedio 0,6597 (brecha 0,014, la más baja). El XGBoost oficial sigue ganando |
| 10 | **Etiqueta de tres clases**: el modelo aprende "mantuvo", "vendió parte" y "vendió todo", y la probabilidad de vender es la suma de las dos ventas | `sold` junta dos comportamientos distintos; verlos por separado podría ayudar a separar a quien vende | No cambió: 0,6593 frente a 0,6595. Brecha 0,016, calibración peor (1,058) |

El detalle de cada resultado está en `docs/experimentos.md`, sección 3, y los números en `reports/tuning.csv`.

**Lo que llevamos:** quince pruebas y ninguna pasó de 0,6636; las que no quitan información quedan entre 0,6573 y 0,6612, una franja del tamaño del ruido. El límite está en la información del cuestionario, no en el ajuste del modelo.

## Decisiones tomadas

- **Restricciones monótonas.** Si cuestan 0,004 de AUROC o menos y no empeoran la calibración, nos quedamos con ellas. Es la misma lógica de la regla del ganador: si la diferencia es ruido, gana el modelo más fácil de explicar.
- **Pesos por clase.** No probamos la pérdida ponderada, que le da más peso a quien vendió, porque el protocolo (sección 5) prohíbe los pesos por clase. La pérdida focal va sin su parte de peso por clase.
- **Parada temprana en todos los pasos que siguen.** Mejoró la calibración sin costo.

## Cierre del plan

- **Hicimos** los pasos 1, 2, 5, 6, 8, 9 y 10. Ninguna prueba pasó de 0,6636.
- **No hicimos** los pasos 3 y 4. Con el visto bueno del tutor cerramos las pruebas, porque más ajuste no iba a subir el AUROC.
- **Configuración final:** XGBoost con parada temprana y poda (protocolo, sección 7). La medimos una sola vez en el 20 % de prueba: AUROC 0,670.

**Diseño de las redes en PyTorch (paso 6).** Las conectamos con **skorch**, una librería que hace que una red de PyTorch funcione como un modelo de scikit-learn, para medirlas con las mismas reglas.

| Red | Cómo es | Por qué |
|---|---|---|
| Simple | Dos capas, *dropout* (apaga neuronas al azar al entrenar) y parada temprana | Muestra si a la red de antes le faltaban esas protecciones |
| Con *embeddings* | Cada tramo de ingreso o activos aprende su propio valor | Los tramos no son números con distancias iguales |
| *Wide & deep* | Una parte lineal, como la regresión logística, más una parte profunda | La logística sola ya da 0,646 |

Cada red se prueba con dos funciones de pérdida, es decir, la fórmula del error que la red intenta bajar: la estándar (entropía cruzada) y la focal (Lin et al., 2017). La focal se concentra en los casos difíciles. No esperamos que superen al boosting: en tablas como la nuestra suele ganar el boosting (Grinsztajn et al., 2022).

**Reparto original del plan:** Dilan el boosting (pasos 1 a 3), Luis Random Forest y variables (pasos 4 y 5), y las redes (paso 6) entre Juan y Dilan.

## Referencias

- Bawalle, A. A., Khan, M. S. R., & Kadoya, Y. (2025). Overconfidence, financial literacy, and panic selling: Evidence from Japan. *PLOS ONE, 20*(3), e0315622.
- Grinsztajn, L., Oyallon, E., & Varoquaux, G. (2022). Why do tree-based models still outperform deep learning on typical tabular data? *NeurIPS 35*.
- Lin, T.-Y., Goyal, P., Girshick, R., He, K., & Dollár, P. (2017). Focal loss for dense object detection. *ICCV 2017*.
