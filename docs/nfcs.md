# Tabla de la NFCS 2018

Código en `bolsalab/nfcs.py`, pruebas en `tests/test_nfcs.py`.

## Qué es y para qué la usamos

La NFCS es una encuesta de FINRA, el ente que vigila a los corredores de bolsa en Estados Unidos. En julio de 2018 le preguntó a 2.003 inversionistas qué hicieron cuando la bolsa cayó cerca de 10 % en febrero de ese año. Las mismas personas respondieron otra parte de la encuesta (State-by-State) con las tres preguntas de conocimiento financiero que usa Japón, cuánto creen saber, su tolerancia al riesgo y sus datos personales.

Es la fuente más parecida a la encuesta japonesa que encontramos, por eso es la primera pieza del dataset multipaís. Con ella vamos a ver si lo que aprende el modelo en Japón sirve en otro país.

Los archivos no se comparten ni se suben al repo: los términos de FINRA lo prohíben. Cada uno los baja de https://www.finrafoundation.org/knowledge-we-gain-share/nfcs/data-and-downloads y deja los dos zip, sin descomprimir, en `data/external/crash/nfcs_investor/raw/`:

- `Inv-Data-and-Data-Info-2018.zip`
- `2018-SxS-Data-and-Data-Info.zip`

## Lo que hicimos

**1. Unimos las dos partes por persona** con `NFCSID`. Las 2.003 personas encontraron su fila. 
Ojo: 9 preguntas tienen el mismo código en las dos partes y preguntan cosas distintas (`A3` es "tiene inversiones fuera de retiro?" en una y "sexo" en la otra), así que llevan el sufijo `_inv` o `_state`.

**2. Dejamos a quien dijo qué hizo en la caída** (pregunta D20): 1.942 personas. Salen 43 que respondieron "no sabe" y 18 "prefiere no decir". Después sacamos 14 más que no calificaron su conocimiento (ver paso 6), y quedan **1.928**.

No filtramos por las inversiones que tenían porque esa pregunta es de julio, después de la caída. Filtrar ahí sacaría a quien vendió todo en febrero, que es justo lo que queremos predecir. Tampoco hacía falta: la encuesta solo dejó seguir a quien tenía inversiones.

**3. Construimos `sold`:** 1 si vendió (86 personas, 4,5 %) y 0 si compró (392) o no hizo nada (1.450). Quien compró va en 0 porque no vendió, igual que en Japón, donde solo hay dos grupos: vendió o mantuvo.

**4. Pasamos los datos personales a la forma de Japón.** Usamos los mismos nombres y, cuando había dos opciones, la que más se parece a la pregunta japonesa.

| Variable | Pregunta NFCS | Cómo queda |
|---|---|---|
| `age` y `age_squared` | A3Ar_w | El archivo público solo trae la edad en 6 rangos. Usamos el punto medio de cada uno (21, 29,5, 39,5, 49,5 y 59,5) y 70 para "65 o más" |
| `male` | A3 | 1 si es hombre |
| `university` | A5 | 1 si tiene pregrado o posgrado. El técnico de 2 años no cuenta |
| `married` | A6 | 1 si está casado |
| `has_children` | A11 | 1 si tiene hijos, dependan o no de él. En Japón la pregunta es "tiene hijos?", sin importar si dependen |
| `employed` | A9 | 1 si es independiente o trabaja tiempo completo o medio tiempo. Así agrupa a los empleados el propio cuestionario |

**5. Las tres preguntas de conocimiento.** La NFCS hace las mismas tres que la encuesta japonesa, las clásicas de Lusardi y Mitchell. Cada una queda en 1 si acertó y 0 si no.

| Variable | Pregunta NFCS | Acertaron |
|---|---|---|
| `knows_interest` | M6: $100 al 2 % durante 5 años, ¿más, igual o menos de $102? | 1.674 |
| `knows_inflation` | M7: interés del 1 % e inflación del 2 %, ¿compra más, igual o menos? | 1.522 |
| `knows_diversification` | M10: ¿una sola acción es más segura que un fondo? (falso) | 1.385 |

"No sabe" y "prefiere no decir" cuentan como 0. Así lo hacen los estudios con estas preguntas, y quitarlos nos haría perder casi una de cada cinco personas. Llama la atención que en diversificación muchas más personas dijeron "no sabe" que en interés (359 contra 91, antes de sacar a las 14 del paso 6).

**6. Confianza y exceso de confianza.** La NFCS pregunta "del 1 al 7, ¿cómo califica su conocimiento sobre finanzas?" (M4). Japón usa una escala de 1 a 5, así que la convertimos en proporción y redondeamos:

| NFCS | 1 | 2 | 3 | 4 | 5 | 6 | 7 |
|---|---|---|---|---|---|---|---|
| `knowledge_confidence` | 1 | 2 | 2 | 3 | 4 | 4 | 5 |

Sacamos a 14 personas que respondieron "no sabe" o "prefiere no decir", porque en Japón esa opción no existe y no queríamos inventarles un valor.

Para `overconfidence` usamos la misma regla del archivo japonés: 1 si marcó 5, o si marcó 4 y acertó 2 o menos preguntas.

**Hallazgo:** los estadounidenses se califican mucho más alto que los japoneses. El 63 % quedó en 4 o 5, contra el 23 % en Japón, y con la misma regla el 48 % tiene exceso de confianza, contra el 7,5 % en Japón. Decidimos como grupo respetar lo que cada persona dijo, sin igualar los países, porque así respondería un usuario en la app y porque esa diferencia es justo lo que queremos estudiar.

Aun así, la relación va en la misma dirección que en Japón: entre quienes tienen exceso de confianza vendió el 6,6 %, y entre los demás, el 2,5 %.

## Lo que hay que tener en cuenta

- En la NFCS vendió el 4,5 % y en Japón el 19,87 %. La caída de 2018 fue mucho menor que la de marzo de 2020.
- La NFCS no separa entre vender todo y vender parte.
- Algunas personas quizás solo tenían bonos. Como mucho son 110 (5,7 %).
- La edad es aproximada: todos los de un rango quedan con la misma edad, y el 70 de "65 o más" es una decisión nuestra.
- La conversión de la confianza de 1-7 a 1-5 es nuestra. Pasar de 5 a 6 en la NFCS no cambia nada (los dos quedan en 4), y eso afecta quién queda con exceso de confianza.

## Cómo correrlo

```bash
uv run python -m bolsalab.nfcs     # cuántas personas quedan y cuántas vendieron
uv run pytest tests/test_nfcs.py   # se saltan si no tienes los archivos
```
