export const glossaryCopy = {
  searchLabel: "Busca un término",
  searchPlaceholder: "Por ejemplo: inflación",
  count: (shown: number, total: number) => (shown === total ? `${total} términos` : `${shown} de ${total} términos`),
  empty: "No encontramos ese término. Prueba con otra palabra.",
};

export const glossaryTerms: { term: string; definition: string }[] = [
  { term: "Acción", definition: "Una pequeña parte de una empresa. Si a la empresa le va bien, tu parte puede valer más; si le va mal, menos." },
  { term: "Renta fija", definition: "Inversiones que pagan un interés acordado, como los CDT o los bonos. Suelen moverse menos que las acciones." },
  { term: "Fondo de inversión", definition: "Un fondo donde muchas personas juntan su dinero y una entidad lo invierte por todas." },
  { term: "ETF", definition: "Un fondo que se compra y se vende en la bolsa como si fuera una acción, y que suele copiar un índice." },
  { term: "Índice bursátil", definition: "Un número que resume cómo se mueve un grupo de acciones. Sirve para saber si “la bolsa” sube o baja." },
  {
    term: "MSCI COLCAP",
    definition: "El índice principal de la Bolsa de Valores de Colombia: agrupa las acciones más negociadas del país. Reemplazó al antiguo COLCAP en 2021.",
  },
  { term: "Portafolio", definition: "El conjunto de todas tus inversiones." },
  { term: "Diversificación", definition: "Repartir tu dinero entre varias inversiones para que la caída de una pese menos." },
  { term: "Riesgo", definition: "La posibilidad de que una inversión te dé menos de lo que esperabas, o incluso pérdidas." },
  { term: "Volatilidad", definition: "Qué tanto y qué tan rápido sube y baja el precio de una inversión." },
  { term: "Rentabilidad", definition: "Lo que ganas o pierdes con una inversión, normalmente en porcentaje." },
  { term: "Interés compuesto", definition: "Ganar intereses sobre los intereses que ya ganaste. Con el tiempo, hace crecer el dinero cada vez más rápido." },
  { term: "Inflación", definition: "La subida general de los precios. Con inflación, el mismo dinero alcanza para menos." },
  { term: "Dividendo", definition: "Parte de las ganancias que una empresa reparte entre quienes tienen sus acciones." },
  { term: "Liquidez", definition: "Qué tan rápido puedes convertir una inversión en dinero sin perder valor." },
  {
    term: "Caída del mercado",
    definition: "Un periodo en que los precios de muchas inversiones bajan a la vez. Cuando la baja pasa del 20 %, se suele llamar mercado bajista.",
  },
  { term: "Venta por pánico", definition: "Vender en medio de una caída por miedo, sin un plan, muchas veces cerca del punto más bajo." },
  { term: "Horizonte de inversión", definition: "El tiempo que planeas dejar invertido tu dinero antes de necesitarlo." },
];
