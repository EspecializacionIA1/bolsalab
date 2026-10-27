"""Prototipo de BolsaLAB en Streamlit.

La persona responde el cuestionario y ve si es más, igual o menos propensa a
vender en una caída que los inversionistas del estudio, qué respuestas pesaron
y qué puede aprender. No carga datos de ninguna encuesta: solo el modelo de
models/ y los resultados agregados de reports/.

Uso: uv run --group app streamlit run app/app.py
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))  # para importar bolsalab también en Streamlit Community Cloud

import matplotlib  # noqa: E402

matplotlib.use("Agg")  # sin ventanas: Streamlit dibuja la figura en la página
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from bolsalab.modeling.predict import CrashReactionModel  # noqa: E402

REPORTS = ROOT / "reports"
SELLS, HOLDS = "#C0392B", "#1F67BF"

st.set_page_config(page_title="BolsaLAB", page_icon="📉", layout="centered")


@st.cache_resource(show_spinner="Cargando el modelo...")
def load_model() -> CrashReactionModel:
    return CrashReactionModel()


model = load_model()
meta = model.metadata

YES_NO = {"Sí": True, "No": False}
LEVEL_NAMES = ["Bajo", "Medio bajo", "Medio", "Medio alto", "Alto"]
INTEREST = {"Más de $102": "more", "Exactamente $102": "exactly",
            "Menos de $102": "less", "No sé": "dont_know"}
INFLATION = {"Más que hoy": "more", "Lo mismo que hoy": "same",
             "Menos que hoy": "less", "No sé": "dont_know"}
DIVERSIFICATION = {"Verdadero": "true", "Falso": "false", "No sé": "dont_know"}
# Opciones del artículo (Bawalle et al., 2025, sección 2.3); 5 = más confianza, como en los datos.
CONFIDENCE = {"Totalmente de acuerdo": 5, "Algo de acuerdo": 4, "No puedo decir ni sí ni no": 3,
              "Más bien lo contrario": 2, "Totalmente en desacuerdo": 1}

HEADLINES = {
    "more_likely": ("Estás en el tercio que más vende", SELLS),
    "similar": ("Estás en el tercio del medio", "#B9770E"),
    "less_likely": ("Estás en el tercio que menos vende", HOLDS),
}
LESSONS = {
    "interest": ("Interés compuesto",
                 "La respuesta es **más de $102**. El primer año ganas $2 y llegas a $102; desde "
                 "ahí también ganas intereses sobre los intereses. A los cinco años tendrías "
                 "unos $110,41."),
    "inflation": ("Inflación",
                  "La respuesta es **menos que hoy**. Si los precios suben 2 % y tu dinero "
                  "crece 1 %, con la misma plata compras menos."),
    "diversification": ("Diversificación",
                        "La respuesta es **falso**. Una sola empresa puede caer mucho por un "
                        "problema propio. Un fondo reparte el dinero entre muchas empresas, y "
                        "la caída de una pesa menos."),
}

st.title("BolsaLAB")
st.caption("Prototipo académico, Grupo 10, Especialización en IA, Pontificia Universidad "
           "Javeriana. No es asesoría de inversión: nunca recomienda comprar ni vender un activo.")

ask, how = st.tabs(["¿Venderías en una caída?", "Cómo funciona el modelo"])

with ask:
    st.markdown(
        "En marzo de 2020 la bolsa cayó por el COVID-19. En una encuesta a 54.704 "
        "inversionistas de Japón, **1 de cada 5 vendió todo o parte** de sus acciones o fondos "
        "(Bawalle, Khan y Kadoya, 2025). Responde y mira dónde quedarías tú.")

    with st.form("cuestionario"):
        st.subheader("Sobre ti")
        age = st.number_input("Edad", min_value=18, max_value=100, value=30, step=1)
        left, right = st.columns(2)
        male = left.radio("Sexo", ["Mujer", "Hombre"], horizontal=True) == "Hombre"
        university = right.radio("¿Tienes título universitario?", YES_NO, horizontal=True)
        married = left.radio("¿Estás casado(a)?", YES_NO, horizontal=True)
        children = right.radio("¿Tienes hijos?", YES_NO, horizontal=True)
        urban = left.radio("¿Vives en una ciudad grande?", YES_NO, horizontal=True)
        employed = right.radio("¿Tienes empleo?", YES_NO, horizontal=True)

        st.subheader("Tu situación económica")
        st.caption("Frente a la gente de tu país. Es una forma provisional de preguntar, "
                   "mientras tenemos los tramos de ingreso colombianos.")
        income = st.select_slider("Ingreso de tu hogar", LEVEL_NAMES, value="Medio")
        assets = st.select_slider("Tus ahorros e inversiones", LEVEL_NAMES, value="Medio")

        st.subheader("Tres preguntas de finanzas")
        interest = st.radio(
            "1. Tienes $100 en una cuenta de ahorros que paga 2 % de interés al año y nunca "
            "retiras nada. Después de cinco años, ¿cuánto tendrías?", INTEREST, index=None)
        inflation = st.radio(
            "2. Tu cuenta paga 1 % al año y la inflación es de 2 % al año. Dentro de un año, "
            "¿cuánto podrías comprar con ese dinero?", INFLATION, index=None)
        diversification = st.radio(
            "3. ¿Verdadero o falso? \"Comprar acciones de una sola empresa suele dar un "
            "rendimiento más seguro que un fondo de inversión en acciones.\"",
            DIVERSIFICATION, index=None)
        confidence = st.radio("¿Qué tan de acuerdo estás con esta frase? \"Tengo confianza "
                              "en mis conocimientos financieros.\"", CONFIDENCE, index=None)
        sent = st.form_submit_button("Ver mi resultado", type="primary")

    if sent:
        if None in (interest, inflation, diversification, confidence):
            st.warning("Responde las tres preguntas de finanzas y la de confianza.")
        else:
            st.session_state["result"] = model.predict({
                "age": int(age), "male": male, "university": YES_NO[university],
                "married": YES_NO[married], "has_children": YES_NO[children],
                "urban": YES_NO[urban], "employed": YES_NO[employed],
                "income_level": LEVEL_NAMES.index(income) + 1,
                "assets_level": LEVEL_NAMES.index(assets) + 1,
                "interest": INTEREST[interest], "inflation": INFLATION[inflation],
                "diversification": DIVERSIFICATION[diversification],
                "knowledge_confidence": CONFIDENCE[confidence],
            })

    result = st.session_state.get("result")
    if result:
        title, color = HEADLINES[result["category"]]
        st.divider()
        st.markdown(f"<h3 style='color:{color};margin-bottom:0'>{title}</h3>",
                    unsafe_allow_html=True)
        st.markdown("Comparado con los inversionistas japoneses con los que aprendió el modelo. "
                    "No mostramos un porcentaje porque el modelo aprendió en Japón y ese número "
                    "no sería confiable para ti.")

        factors = pd.DataFrame(result["top_factors"])
        st.subheader("Qué pesó en tu resultado")
        fig, ax = plt.subplots(figsize=(6, 0.55 * len(factors) + 0.4))
        shown = factors.iloc[::-1]
        signed = shown["impact"].where(shown["direction"] == "increases", -shown["impact"])
        ax.barh(shown["label"], signed,
                color=[SELLS if d == "increases" else HOLDS for d in shown["direction"]])
        ax.axvline(0, color="#555", linewidth=0.8)
        ax.set_xticks([])
        ax.set_xlabel("← baja la propensión a vender      sube la propensión a vender →")
        for side in ["top", "right", "left"]:
            ax.spines[side].set_visible(False)
        fig.tight_layout()
        st.pyplot(fig)
        plt.close(fig)

        mine = factors[factors["actionable"]]
        situation = factors[~factors["actionable"]]
        if not mine.empty:
            st.markdown("**Lo que puedes trabajar**")
            for _, f in mine.iterrows():
                arrow = "sube" if f["direction"] == "increases" else "baja"
                st.markdown(f"- {f['label']}: {arrow} tu propensión a vender.")
        if not situation.empty:
            st.markdown("**Tu situación** (no depende de ti)")
            for _, f in situation.iterrows():
                arrow = "sube" if f["direction"] == "increases" else "baja"
                st.markdown(f"- {f['label']}: {arrow} tu propensión a vender.")
        st.caption("Esto explica lo que hace el modelo, calculado con SHAP. No dice que esa "
                   "respuesta sea la causa de que alguien venda. Todavía no preguntamos por tu "
                   "actitud ante el riesgo ni por tu visión de corto plazo: usamos la respuesta "
                   "más común en Japón.")
        if result["warnings"]:
            st.info("Tu edad está fuera de las edades de la encuesta japonesa "
                    f"({meta['age_range'][0]} a {meta['age_range'][1]} años). "
                    "Toma el resultado con más cuidado.")

        st.subheader("Qué aprender")
        if not result["failed_questions"] and not result["overconfident"]:
            st.markdown("Acertaste las tres preguntas y tu confianza va de acuerdo con lo que "
                        "sabes. En Japón, quienes acertaban vendieron menos en la caída.")
        for q in result["failed_questions"]:
            topic, text = LESSONS[q]
            with st.expander(f"{topic}: la pregunta que no acertaste"):
                st.markdown(text)
        if result["overconfident"]:
            with st.expander("Confianza frente a conocimiento"):
                st.markdown(
                    "Te sientes más seguro(a) de lo que mostraron tus respuestas. En los datos "
                    "de entrenamiento, de quienes estaban así vendió el 28,4 %; de los demás, "
                    "el 19,2 %. Bawalle et al. (2025) encontraron lo mismo en Japón y lo vimos "
                    "también en EE. UU. (NFCS 2018).")

with how:
    st.subheader("Con qué aprendió")
    st.markdown(
        "Con una encuesta de Rakuten Securities y la Universidad de Hiroshima a inversionistas "
        "de Japón (Bawalle, Khan y Kadoya, 2025, PLOS ONE). Son 54.704 personas que tenían "
        "acciones o fondos en marzo de 2020: el 19,87 % vendió todo o parte. El modelo usa 17 "
        "variables de su cuestionario y aprendió con el 80 % de las personas; el otro 20 % "
        "queda guardado para medirlo una sola vez.")

    st.subheader("Qué modelo ganó")
    benchmark = pd.read_csv(REPORTS / "benchmark.csv")
    names = {"trivial": "Trivial (adivina)", "logistic": "Regresión logística",
             "random_forest": "Random Forest", "xgboost": "XGBoost", "lightgbm": "LightGBM",
             "catboost": "CatBoost", "neural_net": "Red neuronal"}
    table = pd.DataFrame({
        "Modelo": benchmark["model"].map(names),
        "AUROC": benchmark["auroc"].round(3),
        "Variación (±)": benchmark["auroc_sd"].round(3),
    })
    st.dataframe(table, hide_index=True, use_container_width=True)
    st.markdown(
        "Ganó **XGBoost** por la regla que fijamos antes de entrenar: CatBoost quedó a menos "
        "de una variación y gana el más simple. Un AUROC de 0,66 quiere decir que, si tomamos "
        "una persona que vendió y otra que no, el modelo le da más riesgo a la que vendió unas "
        "66 de cada 100 veces. Ajustar más no lo mejoró: el límite está en lo que dice el "
        "cuestionario.")
    if meta.get("test") is None:
        st.info("Este prototipo usa el modelo entrenado con el 80 %. Todavía no lo medimos en "
                "el 20 % guardado.")

    st.subheader("Qué respuestas pesan más")
    st.image(str(REPORTS / "figures" / "shap_importancia.png"))
    st.image(str(REPORTS / "figures" / "shap_beeswarm.png"))
    st.markdown(
        "Las tres preguntas de finanzas, cuando se aciertan, bajan la venta, y sentirse muy "
        "seguro la sube. Es lo que esperábamos por la literatura. Lo que más pesa es el sexo: "
        "en estos datos vendió el 23,6 % de los hombres y el 12,2 % de las mujeres. Ese peso "
        "viene de Japón y es parte de lo que el equipo revisa por grupos.")

    st.subheader("Límites")
    st.markdown(
        "- Aprendió en Japón y lo usarán colombianos. Por eso mostramos tercios y no "
        "porcentajes.\n"
        "- Dos preguntas del modelo, actitud ante el riesgo y visión de corto plazo, todavía no "
        "se hacen: no conocemos su redacción original.\n"
        "- El ingreso y los ahorros se preguntan por nivel frente a la gente del país, de forma "
        "provisional.\n"
        "- En EE. UU. (NFCS 2018) las preguntas de finanzas y el exceso de confianza van en la "
        "misma dirección que en Japón; la prueba completa del modelo allá está pendiente.")
