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

Código en `bolsalab/modeling/groups.py`, tabla en `reports/groups.csv`. Medido con la configuración final (XGBoost con parada temprana y poda) y las predicciones de validación cruzada del entrenamiento (5 particiones, semilla 42), así que no tocamos la prueba.

| Grupo | Personas | Vendió | Predicción media | AUROC | Pendiente de calibración |
|---|---|---|---|---|---|
| Hombres | 29.348 | 23,6 % | 23,5 % | 0,623 | 1,01 |
| Mujeres | 14.415 | 12,2 % | 12,4 % | 0,639 | 0,97 |
| 18 a 39 años | 13.449 | 18,3 % | 18,2 % | 0,693 | 1,08 |
| 40 a 59 años | 22.635 | 18,9 % | 19,0 % | 0,646 | 0,99 |
| 60 años o más | 7.679 | 25,6 % | 25,3 % | 0,585 | 0,78 |
| Ingreso, tramos 1 a 4 | 18.045 | 22,2 % | 22,0 % | 0,658 | 0,96 |
| Ingreso, tramos 5 a 7 | 20.103 | 17,9 % | 18,1 % | 0,653 | 1,04 |
| Ingreso, tramos 8 o más | 5.615 | 19,5 % | 19,2 % | 0,651 | 1,08 |
| **Principiantes** | 1.697 | 31,1 % | 28,1 % | **0,721** | 1,02 |
| Resto | 42.066 | 19,4 % | 19,5 % | 0,653 | 0,99 |

- **Principiantes** (menores de 35 con 0 o 1 aciertos en finanzas) son lo más parecido a nuestro usuario. Ahí el modelo ordena mejor que en cualquier otro grupo (0,721), aunque los subestima un poco: predice 28,1 % y vendieron 31,1 %. Ojo: el grupo se define con preguntas que el modelo también usa, así que el 0,721 dice que ordena bien dentro del grupo, no que sirva más para principiantes en general.
- **Mayores de 60:** es donde peor distingue (0,585) y exagera las probabilidades (pendiente 0,78). Su resultado en la app debe leerse con cautela.
- **En los demás grupos** la predicción media queda a menos de medio punto de lo real.
- **Frente al modelo anterior**, el AUROC casi no cambia y la calibración mejora, salvo en los mayores de 60 y en los tramos de ingreso 1 a 4.
- **Dentro de cada sexo el AUROC baja** porque parte de lo que distingue el modelo es el sexo mismo. Los cortes de edad e ingreso son decisión nuestra, para tener grupos grandes.

**En la prueba final** (el 20 % que el modelo nunca vio, `reports/groups_test.csv`):

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

Los grupos se comportan igual que en la validación: los principiantes siguen siendo el mejor grupo (0,781) y los mayores de 60, el más débil (0,594). El detalle está en `docs/experimentos.md`, sección 4.

## Publicarlo en Streamlit Community Cloud

1. El repositorio debe tener `models/crash_reaction_v1.joblib`, su `.json` y las gráficas de `reports/figures/`.
2. En share.streamlit.io: New app, repositorio `EspecializacionIA1/bolsalab`, rama `main`, archivo `app/app.py`, Python 3.12.
3. Community Cloud usa `app/requirements.txt` antes que el `uv.lock` de la raíz, porque está junto a la app.

Límites del plan gratuito, según la documentación de Streamlit: hasta 2,7 GB de RAM; la app se duerme tras 12 horas sin visitas (conviene abrirla antes de la sustentación); con repositorio privado, solo una app privada.
