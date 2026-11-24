export type PlanActionId = "wait" | "needMoney" | "reason" | "cushion" | "news" | "howDoIKnow" | "talk";

export const planCopy = {
  label: "Reto 2",
  title: "Tu regla antes de vender",
  intro: "Decide hoy, con calma, cómo vas a pensar el día que el mercado caiga. Arma tu regla tocando las opciones.",
  dropQuestion: "Si mis inversiones caen",
  drops: ["10 %", "20 %", "30 %"],
  actionsQuestion: "antes de decidir, voy a",
  suggested: "Para ti",
  otherLabel: "Otra cosa que harás (opcional)",
  ruleTitle: "Mi regla",
  rule: (drop: string, actions: string) => `Si mis inversiones caen ${drop}, antes de decidir voy a ${actions}.`,
  and: "y",
  empty: "Elige al menos una acción para armar tu regla.",
  print: "Imprimir o guardar en PDF",
  privacy: "Tu regla no sale de tu navegador: no la guardamos ni la vemos.",
  note: "BolsaLAB no te dice qué comprar ni qué vender. Esta regla es tuya.",
};

export const planActions: { id: PlanActionId; label: string }[] = [
  { id: "wait", label: "esperar 48 horas" },
  { id: "needMoney", label: "revisar si voy a necesitar ese dinero en los próximos 12 meses" },
  { id: "reason", label: "preguntarme si cambió la razón por la que invertí o solo cambió el precio" },
  { id: "cushion", label: "revisar si tengo un ahorro para emergencias aparte" },
  { id: "news", label: "no decidir solo por una noticia de hoy" },
  { id: "howDoIKnow", label: "preguntarme “¿cómo sé esto?” y buscar una segunda fuente" },
  { id: "talk", label: "hablarlo con alguien de confianza o con un asesor certificado" },
];
