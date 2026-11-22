# ADR-001: Elección de FastAPI + SQLite para el prototipo

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

## Relación con el alcance
Se prioriza la demostración de arquitectura y trazabilidad por sobre la simulación de infraestructura de producción.
