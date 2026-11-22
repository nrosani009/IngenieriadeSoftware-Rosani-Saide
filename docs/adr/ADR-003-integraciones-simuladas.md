# ADR-003: Adaptadores simulados para proveedores y correo

- Estado: Aceptado
- Fecha: 2026-10-28

## Contexto
La consigna contempla integraciones con correo, proveedores y agencias. El prototipo representa esos flujos con entradas y respuestas locales.

## Decisión
Implementar adaptadores simulados para:
- ingestión de correos a través de `/email/ingest`
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

## Relación con el alcance
Las pruebas cubren el procesamiento local de las solicitudes simuladas. La conexión con terceros queda fuera del alcance.
