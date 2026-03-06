## 2026-03-06 - Alcance y fidelidad de la réplica local de Chatwoot
- Contexto: Se quiere construir una réplica local de la API de Chatwoot para entender la estructura de datos y probar integraciones del repositorio.
- Bloqueo: Falta decidir si la réplica cubrirá solo endpoints actualmente consumidos por el repo o un dominio más amplio, y qué fidelidad debe tener (mock mínimo, stub contractual o emulación avanzada).
- Impacto: Esta decisión define arquitectura, tiempo de implementación, diseño de fixtures, estrategia de mantenimiento y confiabilidad de los resultados de análisis.

## 2026-03-06 - Estrategia de contrato de datos para la réplica
- Contexto: El código actual tolera variaciones de payload (`payload`, `data`, `data.payload`) y utiliza un subset persistido en MySQL.
- Bloqueo: Falta decidir si el contrato de la réplica se basa en capturas reales de payloads de Chatwoot, en modelos sintéticos normalizados o en una estrategia híbrida.
- Impacto: Afecta la utilidad de la réplica para descubrir campos reales, detectar cambios de API y sostener tests estables en el tiempo.
