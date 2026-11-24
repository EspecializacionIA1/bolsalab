import type { Answers } from "@/schemas/prediction";

export type BlockId = "about" | "economy" | "knowledge";

type Option = {
  label: string;
  value: Answers[keyof Answers];
};

type QuestionBase = {
  field: keyof Answers;
  block: BlockId;
  title: string;
  why: string;
  hideBlockIntro?: boolean;
};

export type NumberQuestion = QuestionBase & {
  kind: "number";
  min: number;
  max: number;
};

export type ChoiceQuestion = QuestionBase & {
  kind: "choice";
  options: Option[];
};

export type Question = NumberQuestion | ChoiceQuestion;

const yesNo: Option[] = [
  { label: "Sí", value: true },
  { label: "No", value: false },
];

const levels: Option[] = [
  { label: "Bajo", value: 1 },
  { label: "Medio bajo", value: 2 },
  { label: "Medio", value: 3 },
  { label: "Medio alto", value: 4 },
  { label: "Alto", value: 5 },
];

export const intro = {
  title: "Antes de empezar",
  body: 'Son 13 preguntas en tres bloques. Las tres preguntas de finanzas sí tienen una respuesta correcta; si no la sabes, elige "No sé": también nos sirve. Lo demás es sobre ti y no hay respuestas buenas o malas.',
  privacy: "No te pedimos nombre, correo ni documento, y no guardamos tus respuestas.",
  start: "Empezar",
  blockLabel: "Bloque",
  questionsLabel: "preguntas",
};

export const navigation = {
  back: "Atrás",
  next: "Siguiente",
  finish: "Ver mi resultado",
  required: "Elige una opción para seguir.",
  invalidAge: "BolsaLAB es para personas de 18 a 100 años.",
  why: "¿Por qué preguntamos esto?",
  ageLabel: "Tu edad en años",
  progress: (current: number, total: number, block: string) => `Pregunta ${current} de ${total} · ${block}`,
};

export const blocks: Record<BlockId, { title: string; intro?: string; note?: string }> = {
  about: {
    title: "Sobre ti",
  },
  economy: {
    title: "Tu situación económica",
    intro: "Compárate con la gente de tu país. No necesitas cifras exactas.",
  },
  knowledge: {
    title: "Lo que sabes",
    intro: 'Tres preguntas de finanzas que se usan en todo el mundo. Si no sabes la respuesta, elige "No sé": es mejor que adivinar.',
  },
};

export const questions: Question[] = [
  {
    field: "age",
    block: "about",
    kind: "number",
    min: 18,
    max: 100,
    title: "¿Cuántos años tienes?",
    why: "La edad cambia cómo vivimos las caídas: el horizonte, las responsabilidades y la experiencia son distintos a cada edad.",
  },
  {
    field: "male",
    block: "about",
    kind: "choice",
    title: "¿Cuál es tu sexo?",
    why: "En el estudio de Japón, hombres y mujeres reaccionaron distinto en la caída. El estudio solo registró estas dos opciones, por eso el modelo solo puede usarlas.",
    options: [
      { label: "Mujer", value: false },
      { label: "Hombre", value: true },
    ],
  },
  {
    field: "university",
    block: "about",
    kind: "choice",
    title: "¿Tienes título universitario?",
    why: "Ayuda a describir tu perfil frente al de las personas del estudio.",
    options: yesNo,
  },
  {
    field: "married",
    block: "about",
    kind: "choice",
    title: "¿Estás casado(a)?",
    why: "Las decisiones de dinero cambian cuando se comparten.",
    options: yesNo,
  },
  {
    field: "has_children",
    block: "about",
    kind: "choice",
    title: "¿Tienes hijos?",
    why: "Tener a alguien a cargo cambia cómo se ve el riesgo.",
    options: yesNo,
  },
  {
    field: "urban",
    block: "about",
    kind: "choice",
    title: "¿Vives en una ciudad grande?",
    why: "Es parte de tu perfil, igual que en el estudio.",
    options: yesNo,
  },
  {
    field: "employed",
    block: "about",
    kind: "choice",
    title: "¿Tienes empleo?",
    why: "Un ingreso estable cambia cuánto margen sientes en una caída.",
    options: yesNo,
  },
  {
    field: "income_level",
    block: "economy",
    kind: "choice",
    title: "¿Cómo es el ingreso de tu hogar?",
    why: "Cuánto margen tienes cambia cómo se siente una caída.",
    options: levels,
  },
  {
    field: "assets_level",
    block: "economy",
    kind: "choice",
    title: "¿Cuánto tienes en ahorros e inversiones?",
    why: "No es lo mismo una caída con pocos ahorros que con muchos.",
    options: levels,
  },
  {
    field: "interest",
    block: "knowledge",
    kind: "choice",
    title:
      "Tienes $100 en una cuenta de ahorros que paga 2 % de interés al año y nunca retiras nada. Después de cinco años, ¿cuánto tendrías?",
    why: "Mide si conoces el interés compuesto: tu dinero gana intereses sobre los intereses.",
    options: [
      { label: "Más de $102", value: "more" },
      { label: "Exactamente $102", value: "exactly" },
      { label: "Menos de $102", value: "less" },
      { label: "No sé", value: "dont_know" },
    ],
  },
  {
    field: "inflation",
    block: "knowledge",
    kind: "choice",
    title:
      "Tu cuenta paga 1 % al año y la inflación es de 2 % al año. Dentro de un año, ¿cuánto podrías comprar con ese dinero?",
    why: "Mide si conoces la inflación: si los precios suben más que tu dinero, compras menos.",
    options: [
      { label: "Más que hoy", value: "more" },
      { label: "Lo mismo que hoy", value: "same" },
      { label: "Menos que hoy", value: "less" },
      { label: "No sé", value: "dont_know" },
    ],
  },
  {
    field: "diversification",
    block: "knowledge",
    kind: "choice",
    title:
      '¿Verdadero o falso? "Comprar acciones de una sola empresa suele dar un rendimiento más seguro que un fondo de inversión en acciones."',
    why: "Mide si conoces la diversificación: repartir el dinero baja el riesgo.",
    options: [
      { label: "Verdadero", value: "true" },
      { label: "Falso", value: "false" },
      { label: "No sé", value: "dont_know" },
    ],
  },
  {
    field: "knowledge_confidence",
    block: "knowledge",
    kind: "choice",
    hideBlockIntro: true,
    title: '¿Qué tan de acuerdo estás con esta frase? "Tengo confianza en mis conocimientos financieros."',
    why: "Al final comparamos qué tan seguro te sientes con lo que respondiste.",
    options: [
      { label: "Totalmente de acuerdo", value: 5 },
      { label: "Algo de acuerdo", value: 4 },
      { label: "Ni de acuerdo ni en desacuerdo", value: 3 },
      { label: "Algo en desacuerdo", value: 2 },
      { label: "Totalmente en desacuerdo", value: 1 },
    ],
  },
];
