# BolsaLAB

## ¿Qué es esto?

**BolsaLAB** es un proyecto que construye un portafolio de inversión personalizado basado en tu perfil de riesgo real. Te muestra primero cuánto puedes perder antes de decirte cuánto puedes ganar.

## ¿Qué hace diferente?

1. **Pérdidas primero**: Antes de mostrarte rentabilidades, te dice cuánto podrías perder en el peor escenario histórico.
2. **Español claro**: Sin jerga financiera, explica cada decisión con cifras reales de tu caso.
3. **Simulador emocional**: Te pone a vivir una caída del mercado (marzo 2020) y compara lo que hiciste con lo que dijiste que harías.
4. **Copiloto educativo**: Responde tus dudas con información de fuentes oficiales (BVC, SFC, AMV), pero nunca te dice qué comprar.

## Recorrido del usuario

1. **Login**: Ingresa tu nombre (solo para personalización, no se guarda nada)
2. **Perfilamiento**: Responde 5 preguntas sobre capacidad, tolerancia, horizonte, conocimiento y monto inicial
3. **Portafolio**: Obtienes una mezcla personalizada de renta fija, acciones colombianas, fondo global y efectivo
4. **Copiloto**: Pregunta por qué quedó así, cuánto puedes perder, o cómo evaluar una acción
5. **Simulador**: Vive una caída real y observa si tu comportamiento coincide con tu perfil declarado

## Perfiles disponibles

- **Conservador** (score ≤ 7): Renta fija 60%, acciones 15%, fondo global 15%, efectivo 10%
- **Moderado** (score 8-11): Renta fija 35%, acciones 32%, fondo global 25%, efectivo 8%
- **Agresivo** (score ≥ 12): Renta fija 15%, acciones 45%, fondo global 35%, efectivo 5%

## Cómo usarlo

1. Abre `v1/bolsalab-app.html` en un navegador moderno
2. Antes de empezar, configura tu URL de Google Forms en la variable `FORM_URL` (línea 503) para recolectar feedback
3. Navega siguiendo las instrucciones en pantalla

## Importante

- **No es asesoría de inversión**: Esto es un prototipo educativo para la Especialización en IA de la Javeriana.
- **No se guardan datos**: Todo vive en memoria del navegador durante la sesión.
- **Las cifras son ilustrativas**: No tomes decisiones reales basadas en este prototipo.

## Estructura técnica

- **Una sola página HTML**: Todo el código, estilos y lógica están en `bolsalab-app.html`
- **Sin dependencias externas**: Solo fuentes de Google Fonts
- **Totalmente funcional**: Router, estado, simulaciones y animaciones en vanilla JS
- **Responsive**: Incluye navegación inferior para móviles

## Próximos pasos (según feedback)

- Conectar el copiloto a un LLM real para respuestas más dinámicas
- Agregar más episodios históricos al simulador
- Integrar datos reales de mercado vía API
