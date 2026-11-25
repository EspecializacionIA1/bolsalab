type Group = { label: string; soldRate: number };

type GroupSet = { title: string; finding: string; groups: Group[] };

export const studyCopy = {
  intro:
    "Estos son los datos de 10.941 personas del estudio de Japón que usamos para probar el programa. No incluye a nadie que haya usado BolsaLAB: no guardamos respuestas.",
  question: "De cada 100 personas, ¿cuántas vendieron todo o parte cuando la bolsa cayó?",
  ofHundred: "de cada 100",
  everyone: { label: "Todas las personas", soldRate: 0.1987, finding: "Es decir, 1 de cada 5." },
  beginnersNote: "Principiantes: menores de 35 que acertaron una o ninguna de las tres preguntas de finanzas.",
  caveat:
    "Esto describe lo que pasó en el estudio. No quiere decir que ser hombre o tener más edad haga vender: en cada persona se mezclan muchas cosas a la vez.",
  accuracyLink: { label: "Qué tan bien acierta el programa →", href: "/how-it-works" },
  source: "Fuente: datos del estudio de Bawalle, Khan y Kadoya (2025), revista científica PLOS ONE.",
};

export const groupSets: GroupSet[] = [
  {
    title: "Según el sexo",
    finding: "Los hombres vendieron el doble que las mujeres.",
    groups: [
      { label: "Hombres", soldRate: 0.2393 },
      { label: "Mujeres", soldRate: 0.1166 },
    ],
  },
  {
    title: "Según la edad",
    finding: "Las personas de 60 años o más vendieron más que las jóvenes.",
    groups: [
      { label: "18 a 39 años", soldRate: 0.1799 },
      { label: "40 a 59 años", soldRate: 0.1929 },
      { label: "60 años o más", soldRate: 0.2525 },
    ],
  },
  {
    title: "Según el ingreso",
    finding: "Quienes tenían menos ingresos vendieron un poco más.",
    groups: [
      { label: "Ingreso más bajo", soldRate: 0.2216 },
      { label: "Ingreso medio", soldRate: 0.1813 },
      { label: "Ingreso más alto", soldRate: 0.1867 },
    ],
  },
  {
    title: "Según la experiencia",
    finding: "Los principiantes fueron los que más vendieron: 1 de cada 3.",
    groups: [
      { label: "Principiantes", soldRate: 0.3238 },
      { label: "Los demás", soldRate: 0.1937 },
    ],
  },
];
