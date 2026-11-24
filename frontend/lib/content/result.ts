import type { Result } from "@/schemas/prediction";

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

export const comparison =
  "Te comparamos con 54.704 inversionistas de Japón que vivieron la caída de marzo de 2020, cuando el COVID-19 hizo caer las bolsas del mundo. 1 de cada 5 vendió todo o parte. No mostramos un porcentaje porque el modelo es una herramienta de aprendizaje y una cifra exacta daría una falsa precisión.";

export const restart = "Repetir el diagnóstico";
