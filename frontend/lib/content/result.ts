import type { Factor, Result } from "@/schemas/prediction";

type Headline = {
  label: string;
  title: string;
  highlight: string;
  body: string;
};

export const headlines: Record<Result["category"], Headline> = {
  more_likely: {
    label: "El tercio que más vende",
    title: "Ante una caída, tu primer impulso podría ser",
    highlight: "protegerte",
    body: "Tus respuestas se parecen a las del tercio de inversionistas con más tendencia a vender cuando el mercado cae.",
  },
  similar: {
    label: "El tercio del medio",
    title: "Ante una caída, estás",
    highlight: "en el medio",
    body: "Tus respuestas se parecen a las del tercio del medio: ni de los que más venden ni de los que más mantienen.",
  },
  less_likely: {
    label: "El tercio que menos vende",
    title: "Ante una caída, tiendes a",
    highlight: "mantener la calma",
    body: "Tus respuestas se parecen a las del tercio de inversionistas con menos tendencia a vender cuando el mercado cae. Aun así, ninguna tendencia es una garantía: vale la pena tener un plan.",
  },
};

export const tercileBar = {
  label: "Dónde quedas frente a los inversionistas del estudio",
  you: "Tú estás aquí",
  segments: {
    less_likely: "Tiende a mantener",
    similar: "En el medio",
    more_likely: "Tiende a vender",
  } satisfies Record<Result["category"], string>,
};

export const meaning = [
  { title: "Qué significa", body: "Tus respuestas se parecen a las de ese grupo de inversionistas." },
  { title: "Qué no significa", body: "Que vayas a vender, ni que vender sea un error en tu caso." },
];

export const ageWarnings = {
  outsideRange: "Tu edad está fuera de las edades del estudio (18 a 93 años). Toma este resultado con más cuidado.",
  senior: "Con personas de 60 años o más, el modelo acierta menos que con las demás. Toma este resultado con más cuidado.",
};

export const factorsCopy = {
  title: "Lo que más pesó",
  directions: {
    increases: "Te acerca a vender",
    decreases: "Te ayuda a mantener",
  } satisfies Record<Factor["direction"], string>,
  actionable: { title: "Lo que puedes trabajar", body: "Esto cambia si aprendes." },
  situation: { title: "Tu situación", body: "No depende de ti, pero es bueno conocerla." },
  note: "Esto explica cómo llegó el modelo a tu resultado, no por qué haces lo que haces. Ninguna respuesta es buena o mala.",
};

export const comparison =
  "Te comparamos con 54.704 inversionistas de Japón que vivieron la caída de marzo de 2020, cuando el COVID-19 hizo caer las bolsas del mundo. 1 de cada 5 vendió todo o parte. No mostramos un porcentaje porque el modelo es una herramienta de aprendizaje y una cifra exacta daría una falsa precisión.";

export type ProfilePart = "knowledge" | "situation" | "confidence";
export type PartEffect = "increases" | "decreases" | "low";

export const figure = {
  caption: "Cada punta es una parte de tu perfil. Su color muestra si, para el modelo, te acerca a vender o te ayuda a mantener.",
  parts: {
    knowledge: { position: "Arriba", name: "Lo que sabes" },
    situation: { position: "Derecha", name: "Tu situación" },
    confidence: { position: "Izquierda", name: "Tu confianza" },
  } satisfies Record<ProfilePart, { position: string; name: string }>,
  details: {
    knowledge: (correct: number) => `Acertaste ${correct} de 3 preguntas de finanzas.`,
    confidence: (answer: string) => `Respondiste «${answer}».`,
    confidenceHigh: "Es alta frente a tus aciertos.",
    situation: "Edad, ingreso, ahorros y otros datos.",
  },
  effects: {
    increases: "Te acerca a vender",
    decreases: "Te ayuda a mantener",
    low: "Pesó poco en tu caso",
  } satisfies Record<PartEffect, string>,
  label: (parts: string) => `Tu figura: ${parts}.`,
};

export const nextStep = {
  label: "Siguiente paso",
  title: "Arma tu regla para una caída",
  body: "Decide hoy qué vas a revisar antes de tomar una decisión si tus inversiones caen. Unos 2 minutos.",
  action: "Armar mi regla",
  href: "/plan",
};

export const restart = "Repetir el diagnóstico";
