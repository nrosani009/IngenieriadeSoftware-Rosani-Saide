# ADR-006: Resiliencia en integraciones externas mediante Circuit Breaker

**Estado:** Aceptada  
**Fecha:** 2026-11-20 (primer registro verificable en GitHub; no necesariamente fecha de la decisión)
**Última actualización:** 2026-11-22  
**Iteración ADD:** 3 — Diseño del módulo de soporte e integración B2B con agencias de viajes.

## Contexto y problema

Trotamundos debe comunicarse con APIs externas de agencias de viajes y proveedores de transporte para consultar reservas, recibir actualizaciones y facilitar la resolución de problemas.

Estos sistemas son administrados por terceros, por lo que Trotamundos no tiene control sobre su disponibilidad, latencia o comportamiento ante fallas.

Si una API externa deja de responder, las solicitudes podrían permanecer bloqueadas hasta alcanzar su tiempo de espera, consumiendo recursos y afectando otras operaciones del sistema.

Se necesita definir una estrategia de resiliencia que permita detectar fallas recurrentes, limitar las solicitudes hacia proveedores que presentan problemas y mantener el funcionamiento de las capacidades internas que no dependen de ellos.

## Drivers arquitectónicos

- **UC-04:** Integración con la agencia de viajes preferida para la resolución de problemas.
- **QA-02:** Mantener el tiempo de respuesta web por debajo de 800 ms.
- **QA-04:** Disponibilidad global objetivo del 99,99 % mensual.
- **CON-02:** Integración con APIs heterogéneas de terceros.
- **CRN-03:** Aislamiento del dominio interno respecto de los sistemas externos.

## Alternativas consideradas

### Opción 1: Llamadas directas con manejo básico de errores

Los servicios internos realizan solicitudes a las APIs externas y gestionan individualmente los errores que puedan producirse.

**Ventajas:**
- Implementación sencilla.
- No requiere componentes adicionales.
- Menor complejidad inicial.

**Desventajas:**
- Las solicitudes pueden permanecer bloqueadas ante fallas externas.
- No evita realizar nuevas llamadas hacia proveedores que presentan errores recurrentes.
- Puede provocar acumulación de solicitudes y consumo innecesario de recursos.

### Opción 2: Timeouts y reintentos con Exponential Backoff

Cada solicitud establece un tiempo máximo de espera. Ante errores transitorios, se realizan nuevos intentos aumentando progresivamente el intervalo entre ellos.

**Ventajas:**
- Limita la duración de las solicitudes.
- Permite recuperarse de errores transitorios.
- Reduce la frecuencia de reintentos consecutivos.

**Desventajas:**
- Los reintentos pueden aumentar la carga sobre un proveedor que ya presenta problemas.
- No impide continuar enviando solicitudes cuando las fallas son persistentes.
- Puede incrementar el tiempo total de respuesta.

### Opción 3: Circuit Breaker con timeouts y reintentos controlados

Se incorpora un mecanismo que supervisa las llamadas hacia cada proveedor externo y suspende temporalmente las solicitudes cuando detecta fallas recurrentes.

**Ventajas:**
- Evita enviar solicitudes reiteradas hacia servicios que presentan fallas persistentes.
- Reduce el consumo innecesario de recursos.
- Permite aplicar respuestas degradadas cuando un proveedor no está disponible.
- Facilita la recuperación mediante intentos controlados.

**Desventajas:**
- Introduce mayor complejidad de configuración.
- Requiere definir umbrales de fallas y tiempos de recuperación.
- Puede rechazar temporalmente solicitudes hacia un proveedor que ya se haya recuperado.

## Comparación de alternativas

| Criterio | Llamadas directas | Timeouts + reintentos | Circuit Breaker |
|---|---|---|---|
| Complejidad | Baja | Media | Media/Alta |
| Control del tiempo de espera | Básico | Sí | Sí, combinado con timeout |
| Recuperación ante errores transitorios | Limitada | Sí | Sí |
| Protección ante fallas persistentes | Baja | Parcial | Alta |
| Reducción de llamadas innecesarias | No | Parcial | Sí |
| Respuesta degradada | Manual | Manual | Integrable al patrón |

## Decisión

Se adopta el patrón **Circuit Breaker, combinado con timeouts y reintentos controlados mediante Exponential Backoff**, para las comunicaciones salientes hacia APIs de agencias y proveedores externos.

El mecanismo se ubicará en el Proxy de Resiliencia Externa definido en la iteración 3, entre el servicio de integración y los sistemas de terceros.

El Circuit Breaker contempla tres estados:

1. **Closed:** las solicitudes se realizan normalmente y se supervisan los errores.
2. **Open:** cuando se supera un umbral de fallas, se suspenden temporalmente las solicitudes hacia el proveedor afectado.
3. **Half-Open:** transcurrido un intervalo de recuperación, se permiten solicitudes de prueba para determinar si el proveedor puede volver a utilizarse.

Los reintentos se limitarán a errores transitorios y operaciones seguras de repetir, evitando duplicar modificaciones de reservas.

Cuando un proveedor no esté disponible, el sistema podrá informar temporalmente la imposibilidad de consultar información actualizada y mantener accesibles los datos previamente almacenados, identificando su posible desactualización.

Se selecciona esta alternativa porque permite limitar el impacto de fallas externas sobre los servicios internos, priorizando la disponibilidad y la estabilidad frente a la menor complejidad de las llamadas directas.

## Consecuencias

### Positivas

- Reducción de solicitudes innecesarias hacia proveedores con fallas persistentes.
- Menor riesgo de agotamiento de recursos por conexiones bloqueadas.
- Posibilidad de mantener operativas funcionalidades que no dependen del proveedor afectado.
- Recuperación controlada cuando se restablece la disponibilidad externa.

### Negativas

- Mayor complejidad en la configuración de las comunicaciones.
- Necesidad de ajustar umbrales y tiempos de recuperación.
- Posibilidad de rechazar temporalmente solicitudes válidas.
- Las respuestas degradadas pueden contener información desactualizada.

## Validación de la decisión

La solución propuesta deberá evaluarse mediante los siguientes escenarios:

- **Falla persistente:** simular errores consecutivos de una API externa y comprobar que el circuito pase al estado Open.
- **Recuperación:** simular el restablecimiento del proveedor y verificar la transición desde Half-Open hacia Closed.
- **Rendimiento:** analizar que las solicitudes fallidas no provoquen esperas indefinidas ni bloqueen operaciones independientes.
- **Disponibilidad:** comprobar conceptualmente que una falla externa no implique necesariamente la indisponibilidad del panel de reservas.
- **Consistencia:** verificar que los reintentos no generen operaciones duplicadas.

Los valores concretos de timeout, umbral de fallas e intervalo de recuperación deberán definirse durante el diseño detallado o la implementación del prototipo.

**Estado de validación:** Pendiente de evaluación mediante escenarios de falla o pruebas acotadas del prototipo académico. La incorporación de Circuit Breaker no garantiza por sí sola el cumplimiento del 99,99 % de disponibilidad.

## Correspondencia con el prototipo académico

El patrón Circuit Breaker, los timeouts salientes, los reintentos con Exponential Backoff y la DLQ corresponden a la **arquitectura objetivo**. El prototipo no realiza llamadas a agencias externas y, por tanto, **no implementa ni prueba** apertura/cierre del circuito, fallos remotos, recuperación o entrega garantizada.

Actualmente `POST /support` registra una derivación y responde que es simulada; `POST /provider/reservations/{reservation_id}/update` representa una notificación externa inyectada localmente. Estas simplificaciones se describen en [ADR-P03](./ADR-P03-integraciones-simuladas.md). Ni las pruebas locales ni `GET /health` acreditan QA-02 (< 800 ms) o QA-04 (99,99 % mensual); dichos atributos requieren mediciones y pruebas de fallas en un entorno representativo.
