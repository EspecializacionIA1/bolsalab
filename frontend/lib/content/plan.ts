import type { PlanActionId } from "@/schemas/rule";

export const planCopy = {
  back: "← Volver a mi resultado",
  dropQuestion: "Si mis inversiones caen",
  drops: ["10 %", "20 %", "30 %"],
  defaultDrop: "20 %",
  actionsQuestion: "antes de decidir, voy a",
  prefilled: "Marcamos algunas para empezar. Cambia lo que quieras.",
  suggested: "Para ti",
  otherLabel: "Otra cosa que harás (opcional)",
  ruleTitle: "Mi regla",
  rule: (drop: string, actions: string) => `Si mis inversiones caen ${drop}, antes de decidir voy a ${actions}.`,
  and: "y",
  empty: "Elige al menos una acción para armar tu regla.",
  summary: "Ver mi resumen →",
  privacy: "Tu regla se queda en esta pestaña: no la guardamos en ningún servidor.",
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
