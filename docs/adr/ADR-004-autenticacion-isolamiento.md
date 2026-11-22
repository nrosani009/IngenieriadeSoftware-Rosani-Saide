# ADR-004: Autenticación mínima y aislamiento por usuario

- Estado: Aceptado
- Fecha: 2026-10-28

## Contexto
Cada usuario puede consultar y modificar sus propios viajes y reservas. El prototipo demuestra ese aislamiento mediante identidades de prueba.

## Decisión
Usar tokens de demostración (`demo-alice-token`, `demo-bob-token`) asociados a usuarios ficticios y validar el encabezado `Authorization` en las operaciones protegidas. Las consultas a los recursos del usuario se acotan por `owner`.

## Consecuencias
- Ventajas:
  - se prueba claramente el principio de seguridad y aislamiento
  - ayuda a la validación de usuario por recurso
  - simplifica la ejecución local
- Limitaciones:
  - no es OAuth 2.0 ni RBAC real
  - no se persisten secretos ni sesiones reales

## Relación con el alcance
La seguridad implementada es una prueba de concepto académica, no una solución de autenticación para producción.
