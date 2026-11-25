export const howItWorks = {
  data: {
    title: "De dónde sale tu resultado",
    number: "54.704",
    numberLabel: "personas que invertían en la bolsa en Japón",
    body: "Un estudio les preguntó qué hicieron cuando los precios cayeron fuerte en marzo de 2020, al inicio del COVID-19. 1 de cada 5 vendió todo o parte de lo que tenía.",
    how: "Un programa de computador aprendió qué respuestas se parecían más a las de quienes vendieron. Cuando respondes las 13 preguntas, compara tus respuestas con las de esas personas.",
    source: "Fuente: Bawalle, Khan y Kadoya (2025), revista científica PLOS ONE.",
  },
  accuracy: {
    title: "Qué tan bien acierta",
    intro:
      "Lo probamos una sola vez con 10.941 personas que el programa no conocía. Le mostramos parejas: una persona que vendió y otra que no. Así le fue al adivinar cuál de las dos vendió:",
    cards: [
      { value: "2 de cada 3", label: "En general" },
      {
        value: "8 de cada 10",
        label: "Personas que están empezando",
        note: "Menores de 35 que acertaron una o ninguna de las tres preguntas de finanzas. Es un grupo pequeño: 420 personas.",
      },
      { value: "6 de cada 10", label: "Personas de 60 años o más" },
    ],
    closing:
      "Por eso no te damos un porcentaje exacto. Solo te decimos si tus respuestas se parecen más a las de quienes vendieron, a las de quienes no vendieron, o si estás en el medio.",
  },
  limits: {
    title: "Lo que no puede decirte",
    items: [
      { lead: "Lo que vas a hacer.", text: "Te dice a quién te pareces, no lo que harás." },
      { lead: "Por qué actúas como actúas.", text: "Muestra qué respuestas pesaron en el cálculo, no la causa." },
      { lead: "Cómo reaccionan las personas en Colombia.", text: "Aprendió con personas de Japón." },
      {
        lead: "Todo sobre ti.",
        text: "No te preguntamos cuánto riesgo te gusta tomar ni si piensas en el corto plazo. Para esas dos cosas usamos la respuesta más común del estudio.",
      },
      {
        lead: "Con exactitud lo que hizo cada persona.",
        text: "Respondieron a finales de 2023 sobre lo que hicieron en 2020, así que dependía de lo que recordaban.",
      },
    ],
  },
  privacy: {
    title: "Tus datos",
    items: [
      "No te pedimos nombre, correo ni documento.",
      "Tus respuestas se usan para calcular tu resultado y no se guardan en nuestro servidor.",
      "En tu navegador quedan hasta que cierres la pestaña.",
      "BolsaLAB no te dice qué comprar ni qué vender. Es una herramienta para aprender.",
    ],
  },
  team: "Hecho por el Grupo 10 de la Especialización en Inteligencia Artificial de la Pontificia Universidad Javeriana.",
};
