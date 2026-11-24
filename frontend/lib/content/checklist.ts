type Link = { label: string; href: string };

type ChecklistItem = {
  question: string;
  how: string;
  links: Link[];
};

export const checklistCopy = {
  title: "Antes de invertir en Colombia",
  intro: "Siete cosas para revisar. Toca cada una para ver cómo.",
};

export const checklistItems: ChecklistItem[] = [
  {
    question: "¿Tienes un ahorro para emergencias, aparte de lo que vas a invertir?",
    how: "Suele guardarse donde no baje de precio y se pueda sacar rápido. Las cuentas de ahorro y los CDT de entidades inscritas en Fogafín tienen un seguro de hasta $50 millones por persona en cada entidad; los fondos de inversión colectiva no lo tienen.",
    links: [{ label: "Seguro de depósitos de Fogafín", href: "https://www.fogafin.gov.co/seguro-de-depositos-de-fogafin" }],
  },
  {
    question: "¿Estás libre de deudas caras, como las de tarjeta de crédito?",
    how: "Una deuda con intereses altos puede costarte más de lo que esperas ganar invirtiendo.",
    links: [],
  },
  {
    question: "¿Sabes que no vas a necesitar este dinero en los próximos 12 meses?",
    how: "Si lo necesitas pronto, una caída te puede obligar a vender en el peor momento.",
    links: [],
  },
  {
    question: "¿Revisaste que la entidad esté vigilada por la Superintendencia Financiera?",
    how: "Búscala en la lista oficial. Desconfía de quien promete ganancias altas y seguras.",
    links: [
      {
        label: "Lista de entidades vigiladas",
        href: "https://www.superfinanciera.gov.co/publicaciones/61694/industrias-supervisadas/entidades-vigiladas-por-la-superintendencia-financiera-de-colombia/lista-general-de-entidades-vigiladas-por-la-superintendencia-financiera-de-colombia-61694/",
      },
      { label: "Cómo evitar ofertas fraudulentas", href: "https://www.superfinanciera.gov.co/publicaciones/10115714/" },
    ],
  },
  {
    question: "Si alguien te asesora, ¿revisaste que esté inscrito para hacerlo?",
    how: "Quienes asesoran en el mercado de valores deben estar inscritos en el Registro Nacional de Profesionales del Mercado de Valores (RNPMV).",
    links: [{ label: "Qué es el RNPMV", href: "https://www.superfinanciera.gov.co/publicaciones/57706" }],
  },
  {
    question: "¿Sabes cuánto te cobran por invertir?",
    how: "Pregunta por la comisión de administración y los demás costos. Con los años pesan en lo que ganas.",
    links: [],
  },
  {
    question: "¿Tienes claro que puedes perder parte de lo que inviertes?",
    how: "En acciones y fondos el valor sube y baja. Nadie puede garantizarte una ganancia.",
    links: [],
  },
];
