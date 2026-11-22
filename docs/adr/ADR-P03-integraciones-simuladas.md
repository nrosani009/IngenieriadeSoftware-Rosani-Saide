# ADR-P03: Adaptadores simulados para proveedores y correo

- Estado: Aceptado
- Fecha: 2026-10-28

## Contexto
La consigna contempla integraciones con correo, proveedores y agencias. El prototipo representa esos flujos con entradas y respuestas locales.

## Decisión
Implementar adaptadores simulados para:
- ingestión de correos a través de `/email/ingest`
- rechazo de remitentes no autorizados sin consumir su `message_id`; una vez autorizado el remitente, puede reintentarse el mismo mensaje. Las importaciones exitosas sí se deduplican de forma persistente
- actualizaciones de reservas por proveedor mediante `/provider/reservations/{reservation_id}/update`
- clasificación del soporte y derivación a agencia preferida

## Consecuencias
- Ventajas:
  - evita secretos y accesos reales
  - permite probar flujos funcionales completos
  - mantiene el prototipo ejecutable y trazable
- Limitaciones:
  - no hay conector real con Gmail, IMAP, APIs de aerolíneas o agentes de viaje
  - los tiempos y fallas no representan producción

## Correspondencia con la arquitectura objetivo

Este ADR implementa solo simulaciones locales de los flujos previstos en [ADR-005](./ADR-005-acl-adaptadores.md) (ACL y adaptadores B2B), [ADR-006](./ADR-006-circuit-breaker.md) (resiliencia de APIs externas) y [ADR-009](./ADR-009-asistente-virtual.md) (asistente de soporte). No implementa interfaces de agencia reales, Circuit Breaker, reintentos de red ni mensajería distribuida. `enrich_reservation()` aplica una normalización local; no equivale a una ACL completa. `POST /support` registra la agencia indicada sin enviarle el caso.

## Relación con el alcance
Las pruebas cubren el procesamiento local de las solicitudes simuladas. La conexión con terceros queda fuera del alcance.
