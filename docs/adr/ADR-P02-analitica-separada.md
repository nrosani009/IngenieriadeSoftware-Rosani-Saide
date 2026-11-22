# ADR-P02: Separación entre operación y analítica

- Estado: Aceptado
- Fecha: 2026-10-28

## Contexto
El prototipo debe demostrar la separación entre el almacenamiento operativo y el analítico con infraestructura local.

## Decisión
Mantener `trotamundos.db` para transacciones operativas y `analytics.db` para eventos de negocio. La API ejecuta las consultas de resumen sobre el archivo analítico.

## Consecuencias
- Ventajas:
  - Las consultas agregadas no leen la base operativa. Esta separación de almacenamiento representa la decisión de la iteración 2.
- Limitaciones:
  - no hay CDC real ni pipeline ETL completo
  - el resumen agrega eventos locales por tipo, destino y fecha UTC. Las transiciones de confirmada a cancelada se registran como eventos diferenciados según su origen (`manual_cancelled` o `provider_cancelled`) y el indicador `cancellations` suma ambos; enviar otra cancelación a una reserva ya cancelada no incrementa el indicador. Se contabilizan transiciones, no reservas únicas ni reservas creadas directamente como canceladas
  - la escritura analítica es síncrona y posterior al commit operativo. Los errores SQLite se registran y la operación principal puede completarse sin evento analítico. No hay reintentos ni entrega garantizada
  - la separación es de almacenamiento y consultas. La escritura comparte el proceso y puede sumar latencia a la respuesta

## Relación con el alcance
El almacén local sirve para demostrar consultas agregadas sobre eventos del prototipo. Un almacén de datos de producción queda fuera del alcance.
