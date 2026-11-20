# Datos del proyecto

Usamos seis datasets públicos. Ninguno se sube a git: cada integrante los descarga de su fuente y los guarda en `data/external/crash/<carpeta>/`, con el nombre de carpeta de la tabla.

## Para qué usamos cada uno

| Dataset | Carpeta | Para qué lo usamos | Qué mide y cuántos son |
|---|---|---|---|
| **Encuesta japonesa** (Bawalle, Khan y Kadoya, 2025) | `japan_panic_selling_2020` | **Entrenar el modelo** | Qué hicieron 191.762 clientes de un corredor en línea durante la caída de marzo de 2020. Tenían inversiones 54.704; vendieron todo o parte 10.869 (19,87 %) |
| **Panel SCF 2007-2009** (Reserva Federal de EE. UU.) | `scf_panel_2007_2009` | Tabla preparada para comparar fuera de Japón. El modelo no se evaluó ahí | Las mismas 3.857 familias entrevistadas antes (2007) y después (2009) de la crisis. Tenían acciones o fondos 1.563; salieron unas 311 (19,9 %) |
| **Encuesta de Hanspal, Weber y Wohlfart** (EE. UU., abril de 2020) | `us_covid_crash_hanspal_2020` | Candidata para comparar fuera de Japón. No se usó | 4.567 inversionistas; 1.036 redujeron su proporción en acciones |
| **NFCS Investor Survey 2018** (FINRA) | `nfcs_investor` | Ver si los efectos van en la misma dirección que en Japón, y comparar lo que la gente dice que haría con lo que hizo | 87 de 1.942 vendieron en la caída de febrero de 2018. De 128 que dijeron que venderían ante una caída de 20 %, 35 vendieron de verdad |
| **CRR 2009 Retirement Survey** (Boston College) | `crr_2009_retirement_survey` | Ver si los efectos van en la misma dirección | 262 de 1.269 trabajadores de 45 a 59 años pasaron su cuenta de retiro a bonos o efectivo en la crisis de 2008 |
| **Encuesta coreana de fondos** (Chung y Kim) | `korea_fund_investors_2007_2008` | Ver si los efectos van en la misma dirección | De 581 personas que invertían en 2007, 126 ya no invertían en 2008 |

Solo la encuesta japonesa entrena el modelo. No unimos los seis en una tabla porque cada uno mide "vender" de forma distinta y hace preguntas distintas.

## Dónde se descargan y qué permiten sus términos

| Dataset | Fuente | Términos de uso |
|---|---|---|
| Encuesta japonesa | Archivo S1 del artículo: https://doi.org/10.1371/journal.pone.0315622 | El artículo es CC BY; la página no declara una licencia aparte para el archivo |
| Panel SCF 2007-2009 | https://www.federalreserve.gov/econres/scf_2009p.htm | Descarga directa; la página no declara licencia |
| Hanspal, Weber y Wohlfart | Harvard Dataverse: https://doi.org/10.7910/DVN/XP63F9 | CC0, uso libre |
| NFCS Investor Survey | https://www.finrafoundation.org/knowledge-we-gain-share/nfcs/data-and-downloads | Solo uso académico. **Prohibido compartir los archivos**: cada integrante descarga su propia copia |
| CRR 2009 Retirement Survey | https://crr.bc.edu/crr-2009-retirement-survey-data/ | Uso no comercial, dando crédito al Center for Retirement Research at Boston College |
| Encuesta coreana | Mendeley Data: https://doi.org/10.17632/3mtsnpy3vt.2 | CC BY 4.0 |

## Límites que conviene tener presentes

- No hay datos individuales de Colombia: el modelo aprende de inversionistas de otro país.
- En la encuesta japonesa, las personas respondieron a finales de 2023 sobre lo que hicieron en marzo de 2020.
- El panel SCF no trae las preguntas de conocimiento financiero ni de confianza, así que la prueba en EE. UU. solo cubre la parte demográfica del modelo.
