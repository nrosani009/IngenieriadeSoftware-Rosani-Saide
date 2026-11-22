# ADR-003: Comunicación asíncrona mediante Event Broker

**Estado:** Aceptada  
**Fecha:** Pendiente de registrar
**Última actualización:** 2026-11-22  
**Iteración ADD:** 1 — Definición de la estructura macro y arquitectura de referencia.

## Contexto y problema

Trotamundos debe importar reservas automáticamente desde correos electrónicos y APIs de proveedores externos, procesarlas y actualizar los itinerarios de los usuarios.

La plataforma debe soportar 2 millones de usuarios activos semanales, con picos de demanda durante contingencias de viaje. Además, las actualizaciones provenientes de fuentes externas deben reflejarse en la aplicación en menos de 5 minutos.

Se necesita definir un mecanismo de comunicación que permita desacoplar la recepción de información del procesamiento de reservas, evitando que las demoras de servicios externos bloqueen el funcionamiento del sistema.

## Drivers arquitectónicos

- **UC-01:** Importación y centralización automática de reservas.
- **QA-01:** Actualizaciones reflejadas en menos de 5 minutos.
- **QA-05:** Escalabilidad ante picos de demanda.
- **CON-02:** Integración con APIs externas heterogéneas.

## Alternativas consideradas

### Opción 1: Comunicación síncrona mediante APIs REST

El módulo de ingesta envía solicitudes directamente al servicio de procesamiento de reservas y espera su respuesta.

**Ventajas:**
- Implementación sencilla.
- Flujo de ejecución directo.
- Menor cantidad de componentes de infraestructura.

**Desventajas:**
- Mayor acoplamiento temporal entre servicios.
- Las demoras del procesamiento pueden bloquear las solicitudes.
- Menor capacidad de absorber picos sin mecanismos adicionales.

### Opción 2: Mensajería asíncrona mediante RabbitMQ

El módulo de ingesta publica mensajes en un broker, desde donde los servicios consumidores los procesan independientemente.

**Ventajas:**
- Desacoplamiento entre productores y consumidores.
- Permite distribuir tareas entre múltiples consumidores.
- Facilita el procesamiento diferido y la absorción de picos mediante colas.
- Ofrece mecanismos de confirmación y reencolado de mensajes.

**Desventajas:**
- Requiere administrar un componente adicional.
- Introduce consistencia eventual.
- Necesita políticas de reintentos, deduplicación y manejo de mensajes fallidos.

### Opción 3: Streaming de eventos mediante Apache Kafka

Los eventos se publican en un registro distribuido que permite su consumo por distintos servicios.

**Ventajas:**
- Alta capacidad de procesamiento de eventos.
- Retención y reproducción de eventos.
- Facilita la integración de múltiples consumidores independientes.

**Desventajas:**
- Mayor complejidad de configuración y operación para el alcance del trabajo práctico.
- Requiere administrar particiones, consumidores y políticas de retención.
- Sus capacidades de streaming exceden las necesidades iniciales del procesamiento de reservas.

## Comparación de alternativas

| Criterio | REST síncrono | RabbitMQ | Kafka |
|---|---|---|---|
| Desacoplamiento temporal | Bajo | Alto | Alto |
| Absorción de picos | Limitada | Mediante colas | Mediante registro de eventos |
| Complejidad operativa | Baja | Media | Alta |
| Reintentos | Implementación propia | Soporte mediante colas y políticas | Reprocesamiento y gestión del consumidor |
| Reproducción histórica | No nativa | No es su enfoque principal | Sí |
| Adecuación al procesamiento de tareas | Media | Alta | Media |

## Decisión

Se propone adoptar una **arquitectura de comunicación asíncrona basada en RabbitMQ** para desacoplar la ingesta del procesamiento de reservas.

El módulo de ingesta publicará mensajes con la información recibida desde correos electrónicos y proveedores externos. El servicio de integración y ciclo de vida consumirá estos mensajes para procesarlos y actualizar las reservas correspondientes.

Se selecciona RabbitMQ frente a Kafka porque el escenario principal requiere distribuir tareas de procesamiento y absorber variaciones de carga, sin necesidad inicial de conservar un historial reproducible de eventos.

La comunicación asíncrona se utilizará para el procesamiento de reservas. Las operaciones interactivas del panel podrán continuar utilizando APIs síncronas, según sus necesidades de respuesta.

## Consecuencias

### Positivas
- Menor dependencia temporal entre ingesta y procesamiento.
- Posibilidad de distribuir el procesamiento entre consumidores.
- Mayor capacidad para absorber picos transitorios de mensajes.
- Separación entre operaciones interactivas y procesamiento en segundo plano.

### Negativas
- Mayor complejidad respecto de la comunicación síncrona.
- Necesidad de gestionar mensajes duplicados y fallidos.
- Posibles retrasos entre la recepción y la actualización de reservas.
- Dependencia de la disponibilidad del broker.

## Validación de la decisión

Para evaluar la solución propuesta se consideran los siguientes aspectos:

- **Actualización:** verificar que el tiempo total de recepción, espera en cola y procesamiento pueda mantenerse por debajo de 5 minutos.
- **Escalabilidad:** analizar el comportamiento de la cola cuando aumenta la cantidad de mensajes y consumidores.
- **Resiliencia:** contemplar confirmaciones, reintentos y una cola de mensajes fallidos (Dead Letter Queue).
- **Consistencia:** definir mecanismos de idempotencia para evitar reservas duplicadas ante el reprocesamiento.

**Estado de validación:** Pendiente de evaluación teórica o mediante el prototipo académico. La selección del broker no demuestra por sí sola el cumplimiento de los atributos de calidad.
