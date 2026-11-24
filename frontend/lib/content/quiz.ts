import { questions, type ChoiceQuestion } from "@/lib/content/diagnostic";
import type { Result } from "@/schemas/prediction";

export type KnowledgeField = "interest" | "inflation" | "diversification";
export type Certainty = "guess" | "think" | "sure";

export type QuizQuestion = {
  title: string;
  options: { label: string; value: string }[];
  correct: string;
  answerLabel: string;
  reason: string;
  whyInACrash: string;
};

export const knowledgeFields: KnowledgeField[] = ["interest", "inflation", "diversification"];

const DONT_KNOW = "dont_know";

function diagnosticQuestion(field: KnowledgeField) {
  const question = questions.find((item) => item.field === field) as ChoiceQuestion;
  return {
    title: question.title,
    options: question.options.map((option) => ({ label: option.label, value: String(option.value) })),
  };
}

const whyInACrash: Record<KnowledgeField, string> = {
  interest: "El interés compuesto necesita tiempo. Quien sale del mercado en una caída también deja de acumular sobre lo que ya ganó.",
  inflation: "Pasar todo a efectivo se siente seguro, pero la inflación sigue restando poder de compra mientras esperas.",
  diversification: "Un portafolio repartido suele caer menos de golpe que una sola acción, y eso hace más fácil no decidir por miedo.",
};

export const originalQuestions: Record<KnowledgeField, QuizQuestion> = {
  interest: {
    ...diagnosticQuestion("interest"),
    correct: "more",
    answerLabel: "más de $102",
    reason: "El primer año llegas a $102 y desde ahí ganas intereses sobre los intereses: a los cinco años tendrías unos $110,41.",
    whyInACrash: whyInACrash.interest,
  },
  inflation: {
    ...diagnosticQuestion("inflation"),
    correct: "less",
    answerLabel: "menos que hoy",
    reason: "Tu dinero creció 1 % y los precios 2 %: con la misma plata compras menos.",
    whyInACrash: whyInACrash.inflation,
  },
  diversification: {
    ...diagnosticQuestion("diversification"),
    correct: "false",
    answerLabel: "falso",
    reason: "Una sola empresa puede caer mucho por un problema propio. Un fondo reparte el dinero entre muchas, y la caída de una pesa menos.",
    whyInACrash: whyInACrash.diversification,
  },
};

export const variantQuestions: Record<KnowledgeField, QuizQuestion> = {
  interest: {
    title: "Tienes $200 en una cuenta que paga 5 % de interés al año y nunca retiras nada. Después de tres años, ¿cuánto tendrías?",
    options: [
      { label: "Más de $230", value: "more" },
      { label: "Exactamente $230", value: "exactly" },
      { label: "Menos de $230", value: "less" },
      { label: "No sé", value: DONT_KNOW },
    ],
    correct: "more",
    answerLabel: "más de $230",
    reason: "Con interés compuesto llegas a unos $231,53: cada año ganas intereses también sobre los intereses anteriores.",
    whyInACrash: whyInACrash.interest,
  },
  inflation: {
    title: "Tu cuenta paga 9 % al año y la inflación es de 5 % al año. Dentro de un año, ¿cuánto podrías comprar con ese dinero?",
    options: [
      { label: "Más que hoy", value: "more" },
      { label: "Lo mismo que hoy", value: "same" },
      { label: "Menos que hoy", value: "less" },
      { label: "No sé", value: DONT_KNOW },
    ],
    correct: "more",
    answerLabel: "más que hoy",
    reason: "Tu dinero creció 9 % y los precios solo 5 %: con esa plata compras un poco más.",
    whyInACrash: whyInACrash.inflation,
  },
  diversification: {
    title: "Un fondo tiene 20 empresas que pesan lo mismo. Una cae a la mitad y las demás no se mueven. ¿Cuánto cae el fondo?",
    options: [
      { label: "50 %", value: "half" },
      { label: "10 %", value: "tenth" },
      { label: "2,5 %", value: "small" },
      { label: "No sé", value: DONT_KNOW },
    ],
    correct: "small",
    answerLabel: "2,5 %",
    reason: "Esa empresa era 1 de 20: su caída de la mitad pesa en el fondo 1/20 × 50 % = 2,5 %.",
    whyInACrash: whyInACrash.diversification,
  },
};

export const quizCopy = {
  label: "Reto 1",
  title: "Tres preguntas, otra vez",
  intro: "Unos 2 minutos. Repites las que fallaste y, en las que acertaste, pruebas con otros números.",
  start: "Empezar",
  progress: (current: number, total: number) => `Pregunta ${current} de ${total}`,
  certaintyQuestion: "¿Qué tan seguro estás?",
  certainty: { guess: "Adivino", think: "Creo que sí", sure: "Seguro" } satisfies Record<Certainty, string>,
  pickFirst: "Elige una respuesta primero.",
  correct: (answer: string) => `Correcto: era ${answer}.`,
  dontKnow: (answer: string) => `Elegir “No sé” es mejor que adivinar. Era ${answer}.`,
  wrong: (answer: string) => `Era ${answer}.`,
  sureAndWrong: "Estabas seguro y no era. Le pasa a mucha gente.",
  whyInACrash: "¿Y en una caída?",
  next: "Siguiente",
  finish: "Ver mi resumen",
  summaryTitle: "Tu resumen",
  summary: (sure: number, correct: number, total: number) =>
    `Te sentiste seguro en ${sure} de ${total}. Acertaste ${correct} de ${total}.`,
  summarySureAndWrong:
    "Estuviste seguro en alguna que no era. Antes de una decisión de dinero, pregúntate “¿cómo sé esto?” y busca una segunda fuente.",
};

export const whatIfCopy = {
  title: "¿Y si hubieras acertado esta en el diagnóstico?",
  body: "Mira cuánto pesa esta pregunta en el cálculo del modelo. Saberla ahora no cambia cómo reaccionarías en una caída.",
  action: "Ver si cambia mi tercio",
  loading: "Consultando el modelo…",
  same: "Tu tercio no cambia con esta pregunta: pesan más otras partes de tu perfil.",
  better: (from: string, to: string) => `Con esa respuesta pasarías de ${from} a ${to}.`,
  worse: (from: string, to: string) =>
    `Con esa respuesta pasarías de ${from} a ${to}. El modelo combina muchas respuestas a la vez y a veces se mueven en direcciones inesperadas.`,
  tercileNames: {
    less_likely: "el tercio que menos vende",
    similar: "el tercio del medio",
    more_likely: "el tercio que más vende",
  } satisfies Record<Result["category"], string>,
};

export function isDontKnow(value: string) {
  return value === DONT_KNOW;
}
