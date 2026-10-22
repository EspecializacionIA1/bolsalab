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

**2. Dejamos a quien dijo qué hizo en la caída** (pregunta D20): 1.942 personas. Salen 43 que respondieron "no sabe" y 18 "prefiere no decir".

No filtramos por las inversiones que tenían porque esa pregunta es de julio, después de la caída. Filtrar ahí sacaría a quien vendió todo en febrero, que es justo lo que queremos predecir. Tampoco hacía falta: la encuesta solo dejó seguir a quien tenía inversiones.

**3. Construimos `sold`:** 1 si vendió (87 personas, 4,5 %) y 0 si compró (396) o no hizo nada (1.459). Quien compró va en 0 porque no vendió, igual que en Japón, donde solo hay dos grupos: vendió o mantuvo.

## Lo que hay que tener en cuenta

- En la NFCS vendió el 4,5 % y en Japón el 19,87 %. La caída de 2018 fue mucho menor que la de marzo de 2020.
- La NFCS no separa entre vender todo y vender parte.
- Algunas personas quizás solo tenían bonos. Como mucho son 110 (5,7 %).

## Cómo correrlo

```bash
uv run python -m bolsalab.nfcs     # cuántas personas quedan y cuántas vendieron
uv run pytest tests/test_nfcs.py   # se saltan si no tienes los archivos
```
