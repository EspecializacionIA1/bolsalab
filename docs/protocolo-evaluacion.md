# Protocolo de pruebas y evaluación

BolsaLAB · Grupo 10 · Responsable: Juan Gilberto Ayala (Test Designer) · Versión 0.1, 15 de octubre de 2026

Fijamos estas reglas antes de entrenar. Así como integrantes del equipo comparamos los modelos en igualdad de condiciones y nadie elige el ganador después de ver los resultados. Cada sección dice la regla, su razón con el respaldo que tiene y, si aplica, sus límites. Cuando una regla es decisión nuestra y no viene de un artículo, lo decimos; podemos cambiarla, pero solo antes de entrenar y dejando registro.

## 1. Con quién entrenamos y qué predecimos

**Regla.** Usamos la encuesta de Bawalle, Khan y Kadoya (2025) a clientes de un corredor en línea de Japón. Dejamos a las **54.704 personas** que en marzo de 2020 vendieron todo, vendieron parte o mantuvieron. La variable `sold` vale 1 si vendió todo o parte (`Tot_Panic_Sell` o `Part_Panic_Sell`) y 0 si mantuvo (`Cons_Investor`). Vendieron 10.869, el 19,87 %.

**Por qué**

- Quien no tenía inversiones no podía vender. Si lo mezclamos con quien mantuvo, el modelo aprende a separar inversionistas de no inversionistas.
- Los autores definen la venta de pánico como "the complete or partial liquidation of stocks", y usamos esa misma definición.
- "Operar" no equivale a vender: según Blanchett et al. (2020), quien tiene más saldo mueve más su portafolio; según Bawalle et al. (2025), quien tiene más activos vende todo con menor frecuencia.

**Límites.** Las personas respondieron a finales de 2023 sobre lo que hicieron en marzo de 2020, según nuestra ficha del artículo. Deducimos que `Cons_Investor` significa "mantuvo" a partir de la Tabla 1 y de los conteos.

## 2. Valores que deben dar los datos

**Regla.** Las pruebas de `tests/` comparan la tabla que prepara `dataset.py` con estos valores. Si una falla, nadie entrena hasta encontrar la causa.

**Por qué.** Un filtro mal escrito cambia la población sin que nadie lo note, y cada integrante terminaría entrenando con datos distintos. Calculamos los valores sobre el Excel original del artículo; TRIPOD+AI pide reportarlos (Collins et al., 2024, ítems 6b y 10 según nuestra ficha).

| Prueba | Valor |
|---|---|
| Filas y columnas del archivo | 191.762 × 26 |
| Celdas vacías | 0 |
| Filas con más de una conducta en 1 | 0 |
| Vendió todo / vendió parte / mantuvo | 2.379 / 8.490 / 43.835 |
| Población y personas con `sold = 1` | 54.704 y 10.869 (19,87 %) |
| `Age` | 18 a 94 |
| Las tres preguntas de conocimiento y las seis binarias | 0 o 1 |
| `FinKnw_Confidence` y `Myopic_View` | 1 a 5 |
| `Risk_Aversion` | 0,0 a 1,0, en pasos de 0,1 |
| `H_Income` / `H_Asset` | 12 / 10 tramos |

## 3. Columnas que no entran y columnas repetidas

**Regla**

- Nunca usamos `Tot_Panic_Sell`, `Part_Panic_Sell` ni `Cons_Investor` como entrada.
- De cada grupo de columnas repetidas, el diccionario de variables elige una y explica por qué.
- Para el exceso de confianza usamos `FinLit_Overconfidence`, la columna que usaron los autores. Dejamos fuera `FinLit_Underconfidence`.
- Conservamos las 452 filas que repiten las respuestas de otra: con preguntas cerradas, dos personas pueden responder igual.

**Por qué**

- Kapoor y Narayanan (2023) llaman fuga de información a usar variables que contienen el resultado.
- Con información duplicada, SHAP reparte la importancia entre las copias y la explicación se vuelve confusa.
- Las dos columnas de confianza salen de dos variables que ya entran al modelo. Usamos la de exceso porque la hipótesis H2 la compara con el artículo; ninguna hipótesis usa la otra.

| Columna | Qué contiene |
|---|---|
| `FinLit_Score` / `Fin_Literacy` | Aciertos de 0 a 3 / los mismos aciertos divididos entre 3 |
| `AgeS` / `AgeGroup` | Edad al cuadrado / edad en tres tramos |
| `lH_Income` / `lH_Asset` | Logaritmo del **número de tramo**, no de los yenes |
| `FinLit_Overconfidence` | 1 con confianza 4 y 0 a 2 aciertos, o con confianza 5 |
| `FinLit_Underconfidence` | 1 con confianza 2, o con confianza 1 y 3 aciertos |

**Límites**

- El artículo (Tabla 1) define el exceso de confianza como "menos aciertos que el promedio y confiado". La columna del archivo no sigue ese texto en 3.450 personas, pero su promedio (0,07) coincide con el publicado: los autores la usaron así.
- Todas las respuestas son de 2023, después de la caída. Alguien que vendió y se arrepintió pudo declararse después más averso al riesgo. No podemos corregirlo con código; lo declaramos en el reporte y usamos el panel SCF 2007-2009, que midió antes, como contraste.
- En el cuestionario, 1 en confianza era "totalmente de acuerdo". En el archivo, quien marca 5 acierta más (2,64 frente a 1,98), así que deducimos que el archivo invirtió la escala. La app debe preguntar en el sentido del archivo.

## 4. Cómo partimos los datos

**Regla**

- Apartamos el 20 % como conjunto de prueba, con la misma proporción de ventas. Nadie lo toca hasta evaluar el modelo elegido.
- Con el 80 % hacemos validación cruzada anidada: 5 particiones externas para medir y 3 internas para elegir hiperparámetros.
- Todos usamos la semilla 42.
- Ajustamos escalado y transformaciones dentro del pipeline, solo con los datos de entrenamiento.
- En el panel SCF partimos por familia (`YY1`).

**Por qué**

- Elegir y medir con las mismas particiones infla el resultado. En la simulación de Varma y Simon (2006), con error real de 50 %, la validación simple estimó 37,8 % y la anidada 54,2 %. Cawley y Talbot (2010) describen el mismo sesgo.
- Escalar con todos los datos antes de partir es una fuga (Kapoor y Narayanan, 2023).
- En el panel SCF cada familia aparece cinco veces; sus filas deben quedar juntas (Wieczorek et al., 2022).

**Decisión nuestra:** el 20 %, las 5 × 3 particiones y la semilla 42.

## 5. Desbalance de clases

**Regla.** No corregimos el desbalance: ni SMOTE, ni remuestreo, ni pesos por clase. Si necesitamos atrapar a más personas que venden, movemos el umbral con datos de validación.

**Por qué.** van den Goorbergh et al. (2022) probaron submuestreo, sobremuestreo y SMOTE en un caso con 20 % de eventos, como el nuestro. El AUROC quedó entre 0,79 y 0,80 con y sin corrección, y el intercepto de calibración pasó de 0,06 a entre −1,32 y −1,50 al corregir. Mover el umbral dio la misma sensibilidad.

**Límites.** Ese estudio usa solo regresión logística y no probó pesos por clase; extender su conclusión a todos los modelos es decisión nuestra. Esta regla reemplaza la del paso 9 del estado del arte v1.1 ("pesos por clase y umbral ajustado").

## 6. Métricas

**Regla.** Cada modelo reporta la media y la desviación en las 5 particiones externas. El ganador reporta además su resultado en el conjunto de prueba, con un intervalo de confianza del 95 % para el AUROC (1.000 remuestreos).

**AUROC:** número de 0,5 a 1 que dice qué tan bien el modelo distingue a quien vende de quien no: 0,5 es adivinar al azar y 1 es perfecto.

| Métrica | Qué responde | Respaldo |
|---|---|---|
| **AUROC** (principal) | ¿Pone por encima a quien vendió? | McDermott et al. (2024) |
| AUPRC | ¿Cuántos de los marcados vendieron? Su valor de azar es 0,199 | McDermott et al. (2024) |
| Calibración (intercepto, pendiente y curva) | ¿Un 30 % equivale a 30 de cada 100? | Van Calster et al. (2019) |
| Brier, con beneficio neto | ¿Las probabilidades son buenas y el modelo sirve más que avisar a todos? | Assel et al. (2017); Vickers et al. (2019) |
| Ventas en el 10 % de mayor riesgo | Lectura simple para el profe y la app | Decisión nuestra |

**Por qué.** El AUROC no depende de la proporción de ventas, así que podemos compararlo con el 0,821 de Elkind et al. (2022). La calibración importa porque la app muestra categorías basadas en probabilidades; Van Calster et al. piden al menos 200 eventos para la curva, y el conjunto de prueba tendrá unos 2.170.

## 7. Modelos y regla para elegir el ganador

**Regla.** Entrenamos cinco modelos con los mismos datos y particiones:

| Modelo | Responsable | Por qué entra |
|---|---|---|
| Trivial | Jenny | No aprende nada: le asigna a todas las personas la misma probabilidad, el 19,87 % que vendió en total, y por eso su AUROC es 0,5. Es el piso: un modelo que no lo supera no sirve (Vickers et al., 2019) |
| Regresión logística regularizada | Jenny | La usa el dominio (Bawalle et al., 2025; van Smeden et al., 2019) |
| Random Forest | Luis | Referencia en datos tabulares (McElfresh et al., 2023) |
| XGBoost, LightGBM, CatBoost | Dilan | Los mejores en tablas pequeñas y medianas (Grinsztajn et al., 2022) |
| Red neuronal pequeña | Juan | Único precedente en venta de pánico (Elkind et al., 2022) |

Gana el de mayor AUROC medio, salvo que uno más simple quede a menos de una desviación estándar: entonces gana el simple. Si siguen empatados, decide la pendiente de calibración más cercana a 1. Solo el ganador toca el conjunto de prueba.

**Por qué.** McElfresh et al. (2023) encuentran diferencias pequeñas entre familias en datos tabulares, y en nuestros sondeos la logística quedó a menos de 0,02 del boosting. Un modelo simple se le explica mejor al usuario.

**Decisión nuestra:** el umbral de una desviación, el desempate y estos rangos:

| Modelo | Rangos |
|---|---|
| Logística | `C`: 0,01; 0,1; 1; 10 |
| Random Forest | 300 árboles; `max_depth` 4, 8 o sin límite; `min_samples_leaf` 20 o 100 |
| XGBoost y LightGBM | 300 árboles; `learning_rate` 0,03 o 0,1; `max_depth` 3 o 5 |
| CatBoost | 300 iteraciones; `learning_rate` 0,03 o 0,1; `depth` 4 o 6 |
| Red neuronal | capas (16,) o (32, 16); `alpha` 0,0001 o 0,01; parada temprana |

**Exploración adicional (registrada el 21 de octubre de 2026, antes de correrla).** `bolsalab/modeling/experiments.py` prueba XGBoost, LightGBM y CatBoost con los rangos de arriba y con estos rangos ampliados. Usa la misma partición, la misma validación anidada 5 × 3 y las mismas métricas, y no toca el conjunto de prueba.

| Modelo | Rangos ampliados |
|---|---|
| XGBoost | `learning_rate` 0,01; 0,03 o 0,1; `max_depth` 3, 5 o 7; `subsample` 0,8 o 1; `min_child_weight` 1 o 10 |
| LightGBM | `learning_rate` 0,01; 0,03 o 0,1; `max_depth` 3, 5 o 7; `num_leaves` 15 o 31; `min_child_samples` 20 o 100 |
| CatBoost | `learning_rate` 0,01; 0,03 o 0,1; `depth` 4, 6 u 8; `l2_leaf_reg` 1, 3 o 10 |

Cada combinación se prueba también con cuatro variantes de las 17 variables:

| Variante | Qué cambia |
|---|---|
| `base` | Nada |
| `sin_edad_cuadrado` | Quita `age_squared` |
| `log_ingreso` | Cambia `income_bracket` por log(1 + número de tramo) |
| `edad_x_ingreso` | Agrega `age` × `income_bracket` |

Un experimento puede reemplazar al ganador de la comparación oficial, con la misma lógica de la regla de arriba: lo reemplaza solo si su AUROC medio supera al del ganador por más de una desviación estándar del ganador. Si no, se queda el ganador oficial, porque usa los rangos del protocolo y las 17 variables sin cambios. Esta regla se fijó antes de correr los experimentos.

**Alarmas.** Revisamos si hay fuga ante un AUROC de 0,82 o más (Elkind lo logró con historial de portafolio, no con un cuestionario), ante un intervalo que incluya 0,5 o ante una variable que domine la explicación SHAP.

## 8. Qué ve el usuario

**Regla.** La app muestra si la persona es más, igual o menos propensa a vender que los inversionistas del estudio, nunca la probabilidad. Fijamos los cortes con datos de validación.

**Por qué.** Entrenamos con japoneses y la usarán colombianos. Al cambiar de población, la calibración falla primero (Van Calster et al., 2019; Riley et al., 2024).

**Cortes (registrado el 23 de octubre de 2026, antes de calcularlos).** Con los ajustes del ganador, sacamos la probabilidad de cada persona del entrenamiento con validación cruzada de 5 particiones (semilla 42): cada persona recibe la predicción de un modelo que no la vio. Los dos cortes son los percentiles 33,3 y 66,7 de esas probabilidades:

| Categoría | Probabilidad |
|---|---|
| Más propensa | Igual o mayor al percentil 66,7 |
| Parecida | Entre los dos cortes |
| Menos propensa | Menor al percentil 33,3 |

No usamos el conjunto de prueba. Los cortes se guardan con el modelo.

**Decisión nuestra:** usar tercios. Así cada categoría agrupa a un tercio de los inversionistas japoneses, y la app puede decir "estás en el tercio que más vende" sin mostrar un porcentaje.

**Ingreso y activos en la app (decisión nuestra, provisional).** La persona dice en cuál de cinco niveles está frente a la gente de su país: bajo, medio bajo, medio, medio alto o alto. Cada nivel ocupa el 20 % de la gente y su posición es la mitad de esa franja: 10 %, 30 %, 50 %, 70 % y 90 %. A cada nivel le damos el tramo japonés que contiene esa posición, con la misma función que usamos para la NFCS (`match_brackets_by_position`). Se cambia cuando tengamos los tramos colombianos de la IEFIC.

## 9. Reporte

Seguimos la guía TRIPOD+AI (Collins et al., 2024): población, objetivo, tamaño de muestra, desbalance, métricas y diferencias con la población de la app.

## Referencias

- Assel, M., Sjoberg, D. D., & Vickers, A. J. (2017). The Brier score does not evaluate the clinical utility of diagnostic tests or prediction models. *Diagnostic and Prognostic Research, 1*, 19.
- Bawalle, A. A., Khan, M. S. R., & Kadoya, Y. (2025). Overconfidence, financial literacy, and panic selling: Evidence from Japan. *PLOS ONE, 20*(3), e0315622.
- Blanchett, D., Finke, M. S., & Reuter, J. (2020). *Portfolio delegation and 401(k) plan participant responses to COVID-19* (NBER Working Paper No. 27438).
- Cawley, G. C., & Talbot, N. L. C. (2010). On over-fitting in model selection and subsequent selection bias in performance evaluation. *Journal of Machine Learning Research, 11*, 2079–2107.
- Collins, G. S., et al. (2024). TRIPOD+AI statement. *BMJ, 385*, e078378.
- Elkind, D., Kaminski, K., Lo, A. W., Siah, K. W., & Wong, C. H. (2022). When do investors freak out? Machine learning predictions of panic selling. *The Journal of Financial Data Science, 4*(1), 11–39.
- Grinsztajn, L., Oyallon, E., & Varoquaux, G. (2022). Why do tree-based models still outperform deep learning on typical tabular data? *NeurIPS 35*.
- Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in machine-learning-based science. *Patterns, 4*(9), 100804.
- McDermott, M. B. A., et al. (2024). A closer look at AUROC and AUPRC under class imbalance. *NeurIPS 2024*.
- McElfresh, D., et al. (2023). When do neural nets outperform boosted trees on tabular data? *NeurIPS 36*.
- Riley, R. D., et al. (2024). Evaluation of clinical prediction models (part 2): How to undertake an external validation study. *BMJ, 384*, e074820.
- Van Calster, B., McLernon, D. J., van Smeden, M., Wynants, L., & Steyerberg, E. W. (2019). Calibration: The Achilles heel of predictive analytics. *BMC Medicine, 17*, 230.
- van den Goorbergh, R., van Smeden, M., Timmerman, D., & Van Calster, B. (2022). The harm of class imbalance corrections for risk prediction models. *JAMIA, 29*(9), 1525–1534.
- van Smeden, M., et al. (2019). Sample size for binary logistic prediction models: Beyond events per variable criteria. *Statistical Methods in Medical Research, 28*(8), 2455–2474.
- Varma, S., & Simon, R. (2006). Bias in error estimation when using cross-validation for model selection. *BMC Bioinformatics, 7*, 91.
- Vickers, A. J., van Calster, B., & Steyerberg, E. W. (2019). A simple, step-by-step guide to interpreting decision curve analysis. *Diagnostic and Prognostic Research, 3*, 18.
- Wieczorek, J., Guerin, C., & McMahon, T. (2022). K-fold cross-validation for complex sample surveys. *Stat, 11*(1), e454.
