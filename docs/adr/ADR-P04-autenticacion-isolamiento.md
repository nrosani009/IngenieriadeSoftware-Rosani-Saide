# ADR-P04: Autenticación mínima y aislamiento por usuario

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

## Correspondencia con la arquitectura objetivo

La Iteración 3 propone OAuth 2.0 / OpenID Connect para identidad y autorización granular de itinerarios compartidos (QA-07 y CRN-04). El prototipo utiliza dos tokens fijos y filtra viajes y reservas por propietario (`app/security.py` y `app/main.py`). Los tests verifican escenarios de aislamiento entre Alice y Bob, pero no prueban OAuth/OIDC, RBAC/ABAC completo, delegación de acceso, compartición de itinerarios ni conexión segura con proveedores de correo.

## Relación con el alcance
La seguridad implementada es una prueba de concepto académica, no una solución de autenticación para producción.
