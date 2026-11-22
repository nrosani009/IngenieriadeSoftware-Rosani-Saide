# ADR-009: Asistente virtual de primer nivel basado en reglas y derivación a agencias

**Estado:** Aceptada  
**Fecha:** Pendiente de registrar  
**Última actualización:** 2026-11-22  
**Iteración ADD:** 5 — Diseño del asistente virtual y escalamiento a agencias de viajes.

## Contexto y problema

La segunda entrega del TPE requiere incorporar un módulo avanzado. Se seleccionó la **opción B: asistente virtual de soporte**, para atender consultas sencillas sobre reservas y derivar situaciones complejas a la agencia de viajes preferida.

La Iteración 3 ya define el subsistema de integración B2B mediante una Anti-Corruption Layer (ADR-005) y mecanismos de resiliencia ante fallas externas (ADR-006). El nuevo módulo debe aprovechar esa arquitectura sin duplicar la lógica de integración ni conceder acceso a reservas de otros usuarios.

Se necesita decidir cómo clasificar consultas, responder con información autorizada y registrar la derivación de casos complejos. El prototipo académico debe demostrar estos flujos de forma acotada y verificable, sin exigir infraestructura productiva ni integraciones reales.

## Drivers arquitectónicos

- **UC-06:** Incorporar la opción B, asistente virtual de primer nivel para consultas de estado, incidencias sencillas y derivación de casos complejos. La reprogramación real de reservas no forma parte de la demostración mínima.
- **UC-04:** Facilitar el escalamiento hacia la agencia preferida del usuario.
- **UC-02:** Consultar información de reservas del usuario para generar respuestas contextualizadas.
- **QA-07:** Autorizar el acceso a las reservas consultadas y restringir la exposición de información de terceros.
- **QA-08:** Permitir extender intenciones y reglas sin alterar el núcleo de reservas ni las integraciones B2B.
- **QA-02:** Evitar que una consulta sencilla dependa de llamadas externas; el objetivo web inferior a 800 ms permanece pendiente de medición.
- **QA-04:** Prever una respuesta degradada ante indisponibilidad de agencias; el objetivo de disponibilidad del 99,99 % permanece pendiente de validación.
- **CON-02:** Respetar la heterogeneidad y la falta de control sobre las APIs externas.
- **CON-03:** Definir interfaces y contratos verificables mediante Spec-driven Development.
- **CRN-03:** Aislar las reglas de soporte de los formatos específicos de las agencias.
- **CRN-04:** Verificar la propiedad de reservas y limitar los datos compartidos.

## Alternativas consideradas

### Opción 1: Asistente mediante un modelo de lenguaje externo

Utilizar un servicio de IA generativa para interpretar y responder consultas en lenguaje natural.

**Ventajas:**
- Mayor flexibilidad ante diferentes formulaciones de una consulta.
- Posibilidad de incorporar nuevas intenciones sin definir cada expresión manualmente.
- Respuestas conversacionales más amplias.

**Desventajas:**
- Dependencia de un proveedor y de su disponibilidad.
- Costos, latencia y gestión adicional de credenciales.
- Mayor complejidad para controlar las respuestas y la exposición de datos personales.
- Menor determinismo de las pruebas del prototipo.

### Opción 2: Motor conversacional completo

Implementar un motor de flujos con sesiones, estados, interpretación de intenciones y seguimiento de conversaciones.

**Ventajas:**
- Mayor capacidad para resolver procesos con múltiples pasos.
- Gestión explícita del estado de una conversación.
- Posibilidad de ampliar casos de uso de soporte.

**Desventajas:**
- Mayor esfuerzo de desarrollo, mantenimiento y pruebas.
- Complejidad desproporcionada para la demostración requerida.
- Necesidad de definir más estados, persistencia y transiciones.

### Opción 3: Asistente determinista basado en reglas e intenciones

Clasificar solicitudes mediante reglas explícitas, consultar reservas autorizadas para las intenciones simples y registrar o derivar los casos complejos.

**Ventajas:**
- Comportamiento reproducible y comprobable mediante pruebas automatizadas.
- Menor dependencia de servicios externos para consultas sencillas.
- Delimitación explícita de permisos y responsabilidades.
- Implementación acorde al alcance académico.

**Desventajas:**
- Cobertura limitada de expresiones y lenguaje natural.
- Requiere actualizar reglas y pruebas al incorporar intenciones.
- No resuelve automáticamente reprogramaciones ni incidencias complejas.

## Comparación de alternativas

| Criterio | Modelo externo | Motor conversacional | Reglas deterministas |
|---|---|---|---|
| Complejidad de implementación local | Media/Alta | Alta | Baja |
| Dependencia de terceros | Alta | Variable | Nula para clasificación |
| Reproducibilidad de pruebas | Limitada | Alta, con mayor esfuerzo | Alta |
| Cobertura de lenguaje natural | Amplia, no garantizada | Según configuración | Acotada |
| Control de acceso y exposición de datos | Requiere controles adicionales | Requiere controles explícitos | Control directo en consultas |
| Adecuación al prototipo | Parcial | Baja | Alta |

## Decisión

Se adopta un **asistente virtual determinista basado en reglas e intenciones**, que opera como primer nivel de soporte y reutiliza conceptualmente los servicios de reservas y el módulo de integración B2B definidos previamente.

El flujo propuesto distingue:

1. **Consulta sencilla:** identificar la intención, validar que la reserva pertenece al usuario autenticado, consultar su estado y construir una respuesta local.
2. **Caso complejo:** incluir las solicitudes de reprogramación o cambio de fecha, clasificarlas para escalamiento, registrar el caso y solicitar su derivación mediante el contrato del subsistema B2B y la ACL definidos en el ADR-005; las comunicaciones externas conservan las tácticas de resiliencia del ADR-006.
3. **Intención no resuelta:** solicitar información adicional o derivar la consulta, sin asumir que el asistente comprende cualquier mensaje ni que puede modificar reservas automáticamente.

La interfaz de soporte debe declarar las entradas, respuestas, errores y reglas de autorización. La decisión corresponde a la **arquitectura objetivo**; el prototipo implementa únicamente un subconjunto local y simulado, documentado en ADR-P03 y ADR-P04.

Se priorizan la verificabilidad, la separación de responsabilidades y la simplicidad de implementación frente a una cobertura conversacional más extensa.

## Consecuencias

### Positivas

- Permite demostrar UC-06 y su relación con UC-04 con un alcance controlado.
- Facilita verificar el acceso a reservas propias.
- Reduce dependencias externas para responder consultas simples.
- Permite incorporar nuevas intenciones manteniendo un contrato estable de soporte.
- Reutiliza las decisiones previas de integración y resiliencia sin duplicarlas.

### Negativas

- Las consultas ambiguas pueden no reconocerse correctamente.
- Cada intención adicional requiere ampliar reglas y casos de prueba.
- No se realizan reprogramaciones automáticas de reservas.
- La derivación necesita infraestructura B2B real para convertirse en una operación efectiva.
- Registrar mensajes de soporte exige aplicar criterios de minimización y protección de datos.

## Validación de la decisión

Se consideran los siguientes escenarios:

- **Consulta autorizada:** verificar que el asistente puede informar el estado de una reserva perteneciente al usuario.
- **Aislamiento:** intentar consultar una reserva ajena y comprobar que no se revela información.
- **Escalamiento:** comprobar que un caso complejo, incluidas las solicitudes de reprogramación, se registra e identifica la agencia preferida y que la respuesta indica si la derivación fue simulada. Verificar que no cambia la reserva local.
- **Contrato:** validar las entradas y salidas del endpoint de soporte y los errores esperados.
- **Modificabilidad:** evaluar el impacto de incorporar una nueva regla sin alterar la lógica de reservas o los adaptadores.
- **Rendimiento y disponibilidad:** medir los objetivos QA-02 y QA-04 mediante pruebas representativas en el sistema objetivo; una respuesta local no garantiza estos atributos globales.

### Correspondencia con el prototipo académico

- **Interfaz:** `app/main.py`, `POST /support`, con mensaje, agencia preferida e identificador opcional de reserva.
- **Clasificación:** `app/services.py`, `classify_support()`, mediante términos explícitos; las solicitudes de reprogramación o cambio de fecha se derivan como casos complejos, sin ejecutar el cambio.
- **Consulta autorizada:** `owned_reservation()` verifica la propiedad antes de devolver el estado de la reserva.
- **Casos:** `support_cases` en la base SQLite operacional; se registran clasificación, estado y agencia indicada.
- **Pruebas disponibles:** `test_support_bot_and_agency_escalation` y `test_support_answers_only_for_owned_reservations`, en `tests/test_prototype.py`.
- **Limitaciones:** los tokens son de demostración y el escalamiento a la agencia se simula localmente. No hay integración B2B real, reprogramación automática, motor conversacional completo ni IA generativa.

**Estado de validación:** Los flujos indicados cuentan con pruebas automatizadas definidas en el prototipo; su ejecución independiente y las métricas de calidad globales requieren validación adicional. La simulación no acredita la operación real de la integración B2B.
