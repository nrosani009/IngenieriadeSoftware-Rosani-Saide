# ADR-P01: Elección de FastAPI + SQLite para el prototipo

- Estado: Aceptado
- Fecha: 2026-10-28

## Contexto
El TPE exige un prototipo acotado, verificable y trazable. Debe poder demostrarse con pocos pasos de instalación y pruebas automatizadas, sin depender de infraestructura compleja ni credenciales reales.

## Decisión
Usar Python 3.11, FastAPI y SQLite como base del prototipo. FastAPI genera la documentación interactiva de la API y SQLite permite ejecutar la aplicación con archivos locales.

## Consecuencias
- Ventajas:
  - ejecución simple y portable
  - pruebas rápidas con `pytest`
  - contratos HTTP explícitos y observables
  - claridad para la entrega académica
- Limitaciones:
  - no es una solución de producción
  - queda fuera del alcance la escalabilidad, concurrencia real y alta disponibilidad

## Asociación de reservas a viajes

Se conserva la asignación manual mediante `trip_id`. Como demostración acotada de UC-03, al omitir dicho identificador en la API de reservas o en la ingesta de correo, se busca un único viaje activo del usuario cuyas fechas incluyan el período de la reserva. Si falta la fecha inicial, no hay coincidencias o existen varias, se pide especificar el viaje; no se crea uno automáticamente ni se infieren destinos.

## Archivado y consultas de viajes

El archivado de viajes finalizados se aplica **bajo demanda** al consultar el listado activo (`GET /trips`) o al invocar `POST /trips/archive-finished`; consultar `include_archived=true` no modifica estados. Esta decisión evita un servicio de tareas periódicas para el alcance académico, pero no equivale a archivado independiente del acceso del usuario.

Para evitar consultas N+1, el listado obtiene los viajes del usuario en una consulta y carga conjuntamente sus reservas en una segunda consulta, manteniendo la agrupación y el aislamiento por propietario.

## Relación con el alcance
Se prioriza la demostración de arquitectura y trazabilidad por sobre la simulación de infraestructura de producción.
