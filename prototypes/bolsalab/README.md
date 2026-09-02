# Prototipo BolsaLAB

## Propósito

Este es un **prototipo HTML inicial** para pruebas de usuarios y optimizaciones. No es la aplicación final, es una maqueta funcional para validar la idea central del proyecto antes de construir la arquitectura completa.

## ¿Por qué un prototipo HTML?

- **Pruebas rápidas con usuarios**: Permite mostrar el flujo completo sin backend
- **Validación de concepto**: Confirma que la idea funciona antes de invertir en desarrollo
- **Feedback temprano**: Los usuarios pueden probar y dar retroalimentación sobre el flujo y contenido
- **Referencia de diseño**: Sirve como especificación visual y funcional para el equipo de desarrollo

## La idea central

**BolsaLAB** muestra primero las pérdidas antes que las ganancias. Construye un portafolio personalizado según tu perfil de riesgo y te pone a vivir una caída real del mercado para comparar lo que haces con lo que dijiste que harías.

## Flujo propuesto (v1)

1. **Login simple**: Nombre para personalizar la experiencia
2. **Cuestionario de perfil**: 5 preguntas sobre capacidad, tolerancia, horizonte, conocimiento y monto
3. **Portafolio personalizado**: Muestra primero la peor caída histórica, después el retorno esperado
4. **Copiloto educativo**: Responde preguntas sobre el portafolio (sin dar asesoría de compra)
5. **Simulador de crisis**: Reproduce marzo 2020 y compara tu reacción con tu perfil declarado

## Componentes funcionales en el prototipo

- Perfilamiento con puntuación automática (conservador/moderado/agresivo)
- Cálculo de distribución de activos según perfil
- Visualización de escenarios (pesimista/esperado/optimista)
- Chat con respuestas predefinidas (simula copiloto)
- Animación de caída con toma de decisión y análisis de coherencia

## Versiones disponibles

### v1 - Prototipo inicial
🔗 **[Ver v1 en vivo](https://moonlit-granita-8eec87.netlify.app/)**

Versión base con todas las funcionalidades principales para pruebas iniciales.

### v2 - Iteración con mejoras
🔗 **[Ver v2 en vivo](https://roaring-faun-b76041.netlify.app/)**

Segunda versión con optimizaciones basadas en feedback de usuarios.

### Local

También puedes abrir los archivos `v1/bolsalab-app.html` o `v2/bolsalab-app.html` directamente en tu navegador.

## Limitaciones conocidas (es un prototipo)

- Copiloto con respuestas predefinidas, no usa IA real
- Datos de mercado y perfiles simplificados (solo 3 tipos)
- Un solo episodio histórico en el simulador (marzo 2020)
- Sin persistencia: al refrescar se pierde todo
- Sin validación de inputs ni manejo de errores robusto

## Para el desarrollo real

Este prototipo define:
- **El flujo completo**: Qué pantallas y en qué orden
- **La lógica de perfilamiento**: Cómo se calcula el score y se asigna el portafolio
- **El tono y contenido**: Español claro, pérdidas primero, educativo no comercial
- **La interacción clave**: Simulador que compara declaración vs comportamiento
