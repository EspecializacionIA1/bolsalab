# Prototipo en Streamlit

El prototipo conecta el modelo con una persona: responde el cuestionario y ve si es más, igual o menos propensa a vender en una caída que los inversionistas del estudio, qué respuestas pesaron y qué puede aprender. Lo construimos con Streamlit para la app y SHAP para explicar el modelo.

## Cómo correrlo

```bash
uv sync --group app
uv run python -m bolsalab.modeling.train --prototype   # exporta el modelo sin mirar la prueba
uv run python -m bolsalab.explain                      # SHAP global: tabla y gráficas en reports/
uv run --group app streamlit run app/app.py
```

La app no carga datos de ninguna encuesta. Usa el modelo de `models/` y los resultados agregados de `reports/`, así que se puede publicar sin subir datos.

## Piezas

| Archivo | Qué hace |
|---|---|
| `bolsalab/modeling/train.py --prototype` | Entrena al ganador (XGBoost) solo con el 80 % y lo guarda con los cortes de las categorías y los valores que necesita la app. No mira la prueba; `--final` lo reemplaza después |
| `bolsalab/modeling/predict.py` | De las respuestas a las 17 variables, categoría, factores con SHAP, preguntas falladas y avisos. Lo usan la app y el backend |
| `bolsalab/explain.py` | SHAP global sobre 5.000 personas del entrenamiento |
| `app/app.py` | Cuestionario, resultado con su explicación y qué aprender, y cómo funciona el modelo |
| `app/requirements.txt` | Versiones para Streamlit Community Cloud, las mismas del entrenamiento |
| `tests/test_predict.py` | 8 pruebas, incluida una que llena el cuestionario de la app y revisa el resultado |

## Decisiones

Las reglas están en la sección 8 del protocolo, registradas antes de calcular.

- **Tercios.** Con validación cruzada de 5 particiones sobre el entrenamiento, los cortes quedaron en 15,9 % y 22,1 % de probabilidad. La app nunca muestra ese número.
- **Dos preguntas que no se hacen.** No conocemos la redacción japonesa de `risk_aversion` ni de `short_term_view`. La app usa el valor más común (0,5 y 2), lo dice en pantalla y no las muestra como factor.
- **Ingreso y ahorros por nivel.** Cinco niveles frente a la gente del país, llevados al tramo japonés en la misma posición: ingreso 1→3, 2→4, 3→5, 4→6, 5→8; ahorros 1→1, 2→3, 3→5, 4→7, 5→9. Es provisional hasta tener los tramos de la IEFIC.
- **Las preguntas de finanzas y la de confianza** son las del artículo (Bawalle et al., 2025, sección 2.3), con $ en vez de ¥.
- **Los factores se separan** en "lo que puedes trabajar" (las preguntas de finanzas y la confianza) y "tu situación" (edad, sexo, ingreso y demás), para que el resultado lleve a una acción sin culpar a nadie por lo que no depende de él.
- **SHAP en log-odds.** Con XGBoost, SHAP da cada aporte en la escala interna del modelo; pasarlo a probabilidad pide datos de fondo (documentación de `shap.TreeExplainer`). La app muestra barras sin cifras: hacia dónde empuja cada respuesta y cuánto, comparada con las otras.
- **Sin `streamlit-shap`.** Su README advierte que la gráfica beeswarm se ve mal con matplotlib nuevo. Dibujamos con matplotlib y lo mostramos con `st.pyplot` o como imagen.

## Lo que encontramos con SHAP

Peso medio de cada respuesta en 5.000 personas del entrenamiento (`reports/shap_global.csv`):

| Respuesta | Parte del peso total | Dirección |
|---|---|---|
| Sexo (hombre) | 28 % | Los hombres venden más |
| Acierta diversificación | 15 % | Acertar baja la venta |
| Confianza en lo que sabe | 9 % | Más confianza sube la venta |
| Acierta inflación | 7 % | Acertar baja la venta |
| Edad | 7 % | Sube en las edades altas |
| Aversión al riesgo y visión de corto plazo | 13 % entre las dos | La app no las pregunta todavía |
| Acierta interés compuesto | 5 % | Acertar baja la venta |

- **Las tres preguntas de finanzas suman 27 % y siempre bajan la venta.** Va en la dirección de la hipótesis y de Bawalle et al. (2025).
- **El sexo es lo que más pesa.** En el entrenamiento vendió el 23,6 % de los hombres y el 12,2 % de las mujeres, así que no es un error. Es el resultado que más hay que cuidar al mostrar y lo revisamos en la actividad de desempeño por grupos.
- **La variable de exceso de confianza casi no pesa (1 %), aunque quienes la tienen vendieron más** (28,4 % contra 19,2 %). Se construye con la confianza y las preguntas de finanzas, y SHAP le da su peso a esas dos. Es la advertencia de SHAP con variables relacionadas.
- **Ninguna variable domina sola** (la mayor tiene el 28 %), así que no se activa la alarma del protocolo.
- **SHAP explica lo que hace el modelo, no la causa de la venta.**

## Desempeño por grupos

Código en `bolsalab/modeling/groups.py`, tabla en `reports/groups.csv`. Usamos las predicciones de validación cruzada del entrenamiento (5 particiones, semilla 42), así que no tocamos la prueba.

| Grupo | Personas | Vendió | Predicción media | AUROC | Pendiente de calibración |
|---|---|---|---|---|---|
| Hombres | 29.348 | 23,6 % | 23,5 % | 0,623 | 1,06 |
| Mujeres | 14.415 | 12,2 % | 12,5 % | 0,643 | 1,06 |
| 18 a 39 años | 13.449 | 18,3 % | 18,2 % | 0,693 | 1,13 |
| 40 a 59 años | 22.635 | 18,9 % | 19,0 % | 0,646 | 1,04 |
| 60 años o más | 7.679 | 25,6 % | 25,3 % | 0,588 | 0,85 |
| Ingreso, tramos 1 a 4 | 18.045 | 22,2 % | 22,0 % | 0,660 | 1,02 |
| Ingreso, tramos 5 a 7 | 20.103 | 17,9 % | 18,2 % | 0,653 | 1,07 |
| Ingreso, tramos 8 o más | 5.615 | 19,5 % | 19,0 % | 0,652 | 1,14 |

- **En promedio, el modelo acierta en todos los grupos:** la predicción media queda a menos de medio punto de lo que pasó.
- **Con los mayores de 60 distingue peor** (0,588 contra 0,693 en los de 18 a 39), y su pendiente de 0,85 dice que ahí las probabilidades salen algo exageradas. Es el grupo que más vendió. En la app, el resultado para esta edad debe leerse con más cautela.
- **Dentro de cada sexo el AUROC baja** (0,62 y 0,64 frente a 0,66 en total) porque parte de lo que el modelo distingue es el sexo mismo. Cortamos edades en 40 y 60 y el ingreso en tramos 4 y 7 para tener grupos grandes; es decisión nuestra.

## Publicarlo en Streamlit Community Cloud

1. El repositorio debe tener `models/crash_reaction_v1.joblib`, su `.json` y las gráficas de `reports/figures/`.
2. En share.streamlit.io: New app, repositorio `EspecializacionIA1/bolsalab`, rama `main`, archivo `app/app.py`, Python 3.12.
3. Community Cloud usa `app/requirements.txt` antes que el `uv.lock` de la raíz, porque está junto a la app.

Límites del plan gratuito, según la documentación de Streamlit: hasta 2,7 GB de RAM; la app se duerme tras 12 horas sin visitas (conviene abrirla antes de la sustentación); con repositorio privado, solo una app privada.
