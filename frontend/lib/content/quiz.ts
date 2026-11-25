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

export const knowledgeTopics: Record<KnowledgeField, string> = {
  interest: "Interés compuesto",
  inflation: "Inflación",
  diversification: "Diversificación",
};

const DONT_KNOW = "dont_know";

function diagnosticQuestion(field: KnowledgeField) {
  const question = questions.find((item) => item.field === field) as ChoiceQuestion;
  return {
    title: question.title,
    options: question.options.map((option) => ({ label: option.label, value: String(option.value) })),
  };
}

export const reviewQuestions: Record<KnowledgeField, QuizQuestion> = {
  interest: {
    ...diagnosticQuestion("interest"),
    correct: "more",
    answerLabel: "más de $102",
    reason: "El primer año llegas a $102 y desde ahí ganas intereses sobre los intereses: a los cinco años tendrías unos $110,41.",
    whyInACrash: "El interés compuesto necesita tiempo. Quien sale del mercado en una caída también deja de acumular sobre lo que ya ganó.",
  },
  inflation: {
    ...diagnosticQuestion("inflation"),
    correct: "less",
    answerLabel: "menos que hoy",
    reason: "Tu dinero creció 1 % y los precios 2 %: con la misma plata compras menos.",
    whyInACrash: "Pasar todo a efectivo se siente seguro, pero la inflación sigue restando poder de compra mientras esperas.",
  },
  diversification: {
    ...diagnosticQuestion("diversification"),
    correct: "false",
    answerLabel: "falso",
    reason: "Una sola empresa puede caer mucho por un problema propio. Un fondo reparte el dinero entre muchas, y la caída de una pesa menos.",
    whyInACrash: "Un portafolio repartido suele caer menos de golpe que una sola acción, y eso hace más fácil no decidir por miedo.",
  },
};

export const reviewCopy = {
  title: "Repasa lo que fallaste",
  intro: (count: number) =>
    count === 1
      ? "Es una pregunta. Ves la respuesta y qué tiene que ver con una caída."
      : `Son ${count} preguntas. Ves la respuesta y qué tiene que ver con una caída.`,
  start: "Repasar",
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
  finish: "Terminar",
  summaryTitle: "Cómo te fue",
  summary: (correct: number, total: number) => `Acertaste ${correct} de ${total}.`,
  summaryWithCertainty: (sure: number, correct: number, total: number) =>
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
