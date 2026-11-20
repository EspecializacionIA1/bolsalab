# Comparación de modelos y experimentos

Código en `bolsalab/modeling/train.py` y `bolsalab/modeling/experiments.py`. Resultados en `reports/benchmark.csv` y `reports/experiments.csv`. Las reglas están en `docs/protocolo-evaluacion.md`, secciones 4 a 7. Los resultados con gráficas están en `notebooks/2_modelado/02 - Comparación de modelos.ipynb`.

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

### Paso 8. Búsqueda con Optuna (11 de noviembre de 2026)

En vez de listas cortas de valores, Optuna buscó en rangos completos: 50 combinaciones por partición, 250 en total. Solo XGBoost, con parada temprana y las 17 variables de siempre.

| Prueba | AUROC | Pendiente | Brecha |
|---|---|---|---|
| XGBoost oficial | 0,6601 ± 0,004 | 1,056 | 0,017 |
| XGBoost con poda (paso 2) | 0,6595 ± 0,004 | 1,010 | 0,019 |
| XGBoost con Optuna | 0,6595 ± 0,003 | 1,015 | 0,016 |

- **El AUROC no cambió.** Quedó a 0,0006 del oficial, muy por debajo del 0,004 que contamos como ruido, y lejos de 0,6636. XGBoost oficial sigue siendo el ganador.
- **Ninguna partición quiso árboles profundos.** Podían llegar a profundidad 6 y eligieron 2 o 3.
- **No hay una combinación mejor que las demás.** La velocidad elegida fue de 0,03 a 0,15 y `reg_lambda` de 0,3 a 13,6, según la partición. Cuando valores tan distintos dan el mismo resultado, el ajuste no es lo que limita al modelo.
- **`reg_lambda` alto no era una pista.** En el paso 2 las 5 particiones eligieron el tope de la rejilla (10). Con el rango abierto hasta 20, solo una pasó de 10.
- **Conclusión:** con rejilla o con búsqueda en rangos llegamos al mismo techo. El límite está en la información del cuestionario.

### Paso 5. Variables (12 de noviembre de 2026)

Después de tres formas de ajuste sin mejora, probamos si al modelo le ayuda recibir algunas respuestas ya combinadas. Las ideas salieron del artículo y de mirar, solo con el entrenamiento, qué porcentaje vendió según cada respuesta (`notebooks/3_mejora_auroc/06 - Exploración de variables.ipynb`). Las seis pruebas usan el XGBoost con poda del paso 2; solo cambian las columnas.

| Prueba | AUROC | Diferencia | Brecha | Decisión |
|---|---|---|---|---|
| Sin cambios (paso 2) | 0,6595 ± 0,004 | | 0,019 | Referencia |
| Total de aciertos | 0,6590 ± 0,003 | −0,0006 | 0,017 | No se adopta |
| Confianza sin sustento | 0,6592 ± 0,003 | −0,0003 | 0,019 | No se adopta |
| Hombre con pocos aciertos | 0,6591 ± 0,004 | −0,0004 | 0,017 | No se adopta |
| Poco colchón financiero | 0,6588 ± 0,004 | −0,0008 | 0,019 | No se adopta |
| Tramos como grupos | 0,6573 ± 0,004 | −0,0022 | 0,022 | No se adopta |
| Solo lo que pregunta la app | 0,6520 ± 0,003 | −0,0075 | 0,013 | Las dos preguntas se quedan |

- **Ninguna variable nueva mejoró el modelo.** Las cuatro quedaron a menos de 0,001 de la referencia; la regla pedía más de 0,004.
- **El modelo ya lo sabía.** Los valores SHAP de interacción (`reports/shap_interacciones.csv`) muestran que el modelo ya usaba juntas las preguntas de finanzas y el sexo. Dárselas combinadas no le enseñó nada nuevo.
- **Las dos preguntas que la app no hace sí aportan.** Sin aversión al riesgo ni visión de corto plazo, el AUROC baja 0,0075, casi el doble del umbral. Se quedan en el modelo, y la app debería preguntarlas.
- **Conclusión:** el modelo conserva las 17 variables. Lo que se ve en una tabla no siempre le sirve al modelo: los hombres con pocos aciertos venden 42 %, pero eso ya estaba aprendido.

### Paso 9. Ideas de la literatura (17 de noviembre de 2026)

Probamos las dos ideas de los benchmarks recientes de datos en tabla que no habíamos usado: que cada árbol aprenda con una parte de los datos, y promediar modelos distintos. Las reglas se registraron antes de correrlas (protocolo, sección 7).

| Prueba | AUROC | Brecha | Pendiente | Decisión |
|---|---|---|---|---|
| XGBoost oficial | 0,6601 ± 0,0035 | | 1,056 | Referencia |
| Paso 8, Optuna | 0,6595 ± 0,0032 | 0,016 | 1,015 | |
| **Aleatoriedad en XGBoost** | 0,6611 ± 0,0033 | 0,022 | 1,030 | No pasa 0,6636 |
| **Promedio de XGBoost, CatBoost y logística** | 0,6597 ± 0,0031 | 0,014 | 1,084 | No pasa 0,6636 |

- **La aleatoriedad subió 0,0015 frente a Optuna, pero es ruido.** La regla pedía pasar de 0,6636. Las 5 particiones usaron la aleatoriedad (cada árbol vio entre el 53 % y el 82 % de las personas). Con ella, Optuna eligió árboles más profundos (3 a 6; en el paso 8 fueron 2 o 3) y más lentos (velocidad de 0,012 a 0,036), y la brecha subió de 0,016 a 0,022. Esperábamos lo contrario: que bajara.
- **El promedio no subió el AUROC, pero tiene la brecha más baja de todas las pruebas (0,014).** Promediar suaviza las predicciones y el modelo memoriza menos. A cambio, la calibración empeora: la pendiente pasa a 1,084, porque el promedio acerca todas las probabilidades al centro.
- **Por qué el promedio no ayudó.** Un promedio rinde cuando los modelos se equivocan con personas distintas. Los nuestros aprenden de las mismas 17 respuestas y se equivocan casi igual.
- **Conclusión:** el XGBoost oficial sigue siendo el ganador. Con estas dos ya van 14 pruebas, y las que no quitan información quedan entre 0,6573 y 0,6612. El límite sigue estando en la información del cuestionario.

### Paso 10. Etiqueta de tres clases (17 de noviembre de 2026)

`sold` junta a quien vendió todo (2.379 personas) y a quien vendió parte (8.490). Probamos si el modelo aprende mejor viendo esa diferencia. Usamos el mismo XGBoost con poda del paso 2, con su rejilla, pero aprendiendo tres clases: mantuvo, vendió parte y vendió todo. Para calificarlo sumamos la probabilidad de las dos ventas y la medimos contra `sold`, con las mismas particiones de siempre.

| Prueba | AUROC | Brecha | Pendiente | Decisión |
|---|---|---|---|---|
| XGBoost con poda (paso 2) | 0,6595 ± 0,0037 | 0,019 | 1,010 | Referencia |
| **Etiqueta de tres clases** | 0,6593 ± 0,0031 | 0,016 | 1,058 | No se adopta |

- **No cambió nada.** Bajó 0,0003, muy lejos de los 0,004 que pedía la regla.
- **La brecha bajó un poco (de 0,019 a 0,016), pero la calibración empeoró** (de 1,010 a 1,058).
- **Por qué no ayudó.** Separar la respuesta no agrega información sobre las personas. Si las mismas respuestas del cuestionario empujan a vender parte y a vender todo, el modelo no aprende nada nuevo al verlas por separado.
- **Conclusión:** el XGBoost oficial sigue siendo el ganador. Ya son 15 pruebas, y las 14 que no quitan información quedan entre 0,6573 y 0,6612.

### Decisión: configuración final (18 de noviembre de 2026)

Con el visto bueno y apoyo de nuestro tutor cerramos las pruebas. El modelo final es el **XGBoost con parada temprana y poda del paso 2** (AUROC 0,6595, pendiente de calibración 1,010, brecha 0,019).

- Todas las versiones empatan en AUROC: ninguna pasó de 0,6636.
- En el empate gana la familia más simple, XGBoost, y entre sus versiones la mejor calbrada.
- El detalle y la tabla de candidatos están en el protocolo, sección 7, "Configuración final".

## 4. Prueba final (19 de noviembre de 2026)

Medimos una sola vez el modelo final (XGBoost con parada temprana y poda) en el 20 % de prueba: 10.941 personas que no usamos en ningún momento del proyecto. Lo entrenamos con todo el 80 % desde el commit `97b0da1` y quedó registrado en MLflow como `bolsalab-reaccion-caidas`, versión 1. Desde aquí el modelo no se cambia.

| Métrica | Prueba final | Validación cruzada | Lectura |
|---|---|---|---|
| AUROC | **0,670** (0,658 a 0,682) | 0,6595 ± 0,0037 | Consistente: el intervalo incluye el valor de la validación |
| Vendió en el 10 % de mayor riesgo | **40,8 %** | | El doble del 19,9 % general |
| AUPRC | 0,353 | 0,330 | 1,8 veces el azar (0,199) |
| Brier | 0,149 | 0,150 | Mejor que decir siempre el promedio (0,159) |
| Pendiente de calibración | 1,12 | 1,01 | Las probabilidades salen un poco más apretadas que la realidad |

- **Sin alarmas:** el AUROC está lejos de 0,82 (posible fuga) y el intervalo no incluye 0,5.
- **La prueba sale un poco por encima de la validación** (0,670 frente a 0,660). Está dentro de la variación esperada, y el modelo final aprendió con el 80 % completo.
- **La calibración más apretada no afecta a la app:** la app ubica a cada persona en un tercio según el orden de las probabilidades, no según su valor.

**Por grupos, en el 20 % de prueba** (`reports/groups_test.csv`):

| Grupo | Personas | Vendió | Predicción media | AUROC | Pendiente de calibración |
|---|---|---|---|---|---|
| Hombres | 7.322 | 23,9 % | 23,4 % | 0,625 | 1,09 |
| Mujeres | 3.619 | 11,7 % | 12,5 % | 0,658 | 1,17 |
| 18 a 39 años | 3.368 | 18,0 % | 18,2 % | 0,708 | 1,22 |
| 40 a 59 años | 5.775 | 19,3 % | 18,9 % | 0,657 | 1,12 |
| 60 años o más | 1.798 | 25,3 % | 25,6 % | 0,594 | 0,89 |
| Ingreso, tramos 1 a 4 | 4.545 | 22,2 % | 22,0 % | 0,674 | 1,14 |
| Ingreso, tramos 5 a 7 | 4.982 | 18,1 % | 18,1 % | 0,658 | 1,09 |
| Ingreso, tramos 8 o más | 1.414 | 18,7 % | 18,9 % | 0,673 | 1,20 |
| **Principiantes** | 420 | 32,4 % | 28,1 % | **0,781** | 1,39 |
| Resto | 10.521 | 19,4 % | 19,5 % | 0,661 | 1,08 |

- **Principiantes:** el mejor AUROC (0,781), como en la validación (0,721). Son 420 personas y unas 136 ventas, así que la cifra tiene un margen amplio. El modelo los subestima: predice 28,1 % y vendieron 32,4 %.
- **Mayores de 60:** el punto débil (0,594), igual que en la validación.
- **Ningún grupo queda por debajo de 0,59.**

## Lo que sigue

- Sumar los resultados de las redes en PyTorch cuando se una su código. Ninguna pasó de 0,66, así que no cambian el modelo final.
- Desplegar el modelo congelado: API, app e infraestructura.
