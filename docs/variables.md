# Variables del modelo

El modelo aprende de la encuesta japonesa (54.704 inversionistas). Usa 17 variables de entrada, que salen de 14 preguntas que la app le hace al usuario, y una variable objetivo. `bolsalab/features.py` construye esta tabla.

## Variable objetivo

| Nombre | Columnas del archivo | Valores |
|---|---|---|
| `sold` | `Tot_Panic_Sell`, `Part_Panic_Sell`, `Cons_Investor` | 1 si vendió todo o parte durante la caída de marzo de 2020 (10.869 personas, 19,87 %); 0 si mantuvo |

## Variables que entran

| Variable | Columna del archivo | Valores | Pregunta de la app |
|---|---|---|---|
| `knows_interest` | `Interest_Score` | 0 o 1 | Interés compuesto |
| `knows_inflation` | `Inflation_Score` | 0 o 1 | Inflación |
| `knows_diversification` | `Diversification_Score` | 0 o 1 | Diversificación |
| `knowledge_confidence` | `FinKnw_Confidence` | 1 (nada) a 5 (mucho) | ¿Qué tanto sabe de finanzas? |
| `overconfidence` | `FinLit_Overconfidence` | 0 o 1 | No se pregunta: sale de las preguntas de conocimiento y la confianza |
| `age` | `Age` | 18 a 94 | Edad |
| `age_squared` | `AgeS` | Edad al cuadrado | No se pregunta: sale de la edad |
| `male` | `Gender` | 1 = hombre, 0 = mujer | Sexo |
| `university` | `Uni_Educ` | 0 o 1 | ¿Tiene título universitario? |
| `married` | `Married` | 0 o 1 | ¿Está casado? |
| `has_children` | `Childreen` | 0 o 1 | ¿Tiene hijos? |
| `urban` | `Urban_Dummey` | 0 o 1 | ¿Vive en una ciudad? |
| `employed` | `Employment` | 0 o 1 | ¿Tiene empleo? |
| `income_bracket` | `H_Income` | Tramo 1 a 12 | Tramo de ingreso del hogar |
| `assets_bracket` | `H_Asset` | Tramo 1 a 10 | Tramo de activos financieros |
| `risk_aversion` | `Risk_Aversion` | 0 a 1, en pasos de 0,1 | Preferencia por no arriesgar |
| `short_term_view` | `Myopic_View` | 1 a 5 | Atención al corto plazo |

`age`, `university`, `married`, `has_children` y `employed` también existen en el panel SCF 2007-2009, con los mismos nombres, para probar el modelo fuera de Japón.

## Japón frente a la NFCS 2018 (EE. UU.)

La NFCS tiene 15 de las 17 variables. Las pasamos a los nombres y escalas de Japón en `bolsalab/nfcs.py`; el porqué de cada decisión está en `docs/nfcs.md`.

| Variable | Japón | NFCS | Cómo la igualamos |
|---|---|---|---|
| `sold` | Vendió todo o parte en marzo de 2020 | D20: compró, vendió o nada en febrero de 2018 | 1 si vendió; 0 si compró o no hizo nada |
| `knows_interest` | `Interest_Score` | M6, la misma pregunta | 1 si acertó; "no sabe" cuenta como 0 |
| `knows_inflation` | `Inflation_Score` | M7, la misma pregunta | Igual |
| `knows_diversification` | `Diversification_Score` | M10, la misma pregunta | Igual |
| `knowledge_confidence` | 1 a 5 | M4, de 1 a 7 | En proporción: 1→1, 2→2, 3→2, 4→3, 5→4, 6→4, 7→5 |
| `overconfidence` | Columna del archivo | Se construye | Misma regla de Japón: marcó 5, o marcó 4 y acertó 2 o menos |
| `age` | Edad exacta | A3Ar_w, solo 6 rangos | Punto medio del rango; 70 para "65 o más" |
| `age_squared` | Edad al cuadrado | Se calcula | Desde la edad aproximada |
| `male` | `Gender` | A3 | 1 si es hombre |
| `university` | `Uni_Educ` | A5 | Pregrado o posgrado; el técnico de 2 años no cuenta |
| `married` | `Married` | A6 | 1 si está casado |
| `has_children` | `Childreen` | A11 | 1 si tiene hijos, dependan o no de él |
| `urban` | `Urban_Dummey` | No existe | Solo trae el estado donde vive |
| `employed` | `Employment` | A9 | Independiente, tiempo completo o medio tiempo |
| `income_bracket` | 12 tramos en yenes | A8, 8 tramos en dólares | Por posición dentro de cada país |
| `assets_bracket` | 10 tramos de activos en yenes | B4, valor de las inversiones fuera de retiro, 10 tramos en dólares | Por posición dentro de cada país. No incluye cuentas de retiro |
| `risk_aversion` | 0 a 1; más alto evita más el riesgo | J2, disposición al riesgo de 1 a 10 | Invertida: (10 − J2) / 9. No sabemos la pregunta japonesa |
| `short_term_view` | `Myopic_View` | No existe | No hay una pregunta parecida |

## Decisiones

- **Las tres preguntas de conocimiento van por separado y no sumadas.** Así el modelo aprende cuál pesa más, y la app sabe qué pregunta falló cada persona. El conocimiento financiero es el único predictor con dirección estable en los estudios leídos (Bucher-Koenen y Ziegelmeyer, 2011; Bawalle et al., 2025).
- **La edad entra también al cuadrado.** La venta no cambia en línea recta con la edad: vendió el 28,1 % de quienes tienen 18 a 24 años, entre 17 y 19 % de las edades medias y el 25,5 % desde los 60. La regresión logística solo capta esa forma en U con la edad al cuadrado. Bawalle et al. (2025) también la usan.
- **`overconfidence` usa la columna del archivo,** la misma que usaron los autores, para comparar con su resultado (hipótesis H2). Ver el protocolo, sección 3.
- **`risk_aversion` y `short_term_view` entran** porque la hipótesis H5 necesita la tolerancia al riesgo y Bawalle et al. (2025) asocian la visión de corto plazo con más venta. Falta confirmar la redacción original de esas dos preguntas.
- **Ingreso y activos entran como número de tramo** (1, 2, 3…), que es como los preguntaría la app.

## Columnas que no entran

| Columna | Por qué |
|---|---|
| `Tot_Panic_Sell`, `Part_Panic_Sell`, `Cons_Investor` | Con ellas se construye `sold`. Usarlas como entrada sería una fuga de información |
| `FinLit_Score`, `Fin_Literacy` | Son la suma de las tres preguntas de conocimiento, que ya entran por separado |
| `AgeGroup` | Repite la edad en tres tramos |
| `lH_Income`, `lH_Asset` | Repiten los tramos de ingreso y activos, en logaritmo |
| `FinLit_Underconfidence` | Su regla en el archivo no sigue la definición del artículo, y ninguna hipótesis la usa. Ver el protocolo, sección 3 |
