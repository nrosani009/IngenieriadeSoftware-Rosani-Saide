# ADR-004: Separación de datos transaccionales y analíticos mediante CDC

**Estado:** Aceptada  
**Fecha:** Pendiente de registrar  
**Iteración ADD:** 2 — Diseño de la capa de datos y pipeline analítico.

## Contexto y problema

Trotamundos debe recopilar información sobre tendencias de viajes, destinos y cancelaciones para generar reportes y permitir su explotación analítica.

Estas operaciones requieren consultas complejas sobre grandes volúmenes de datos históricos. Si se ejecutan directamente sobre la base de datos transaccional (OLTP), pueden competir por recursos con las operaciones habituales del panel de reservas.

La arquitectura debe permitir el procesamiento analítico sin degradar significativamente el rendimiento de las operaciones transaccionales, manteniendo la protección de los datos personales de los usuarios.

Se necesita definir una estrategia de extracción y almacenamiento que separe ambas cargas de trabajo.

## Drivers arquitectónicos

- **UC-05:** Recopilación y análisis de tendencias, destinos y cancelaciones.
- **QA-05:** Escalabilidad de la plataforma ante grandes volúmenes de usuarios.
- **QA-06:** Protección de datos personales durante el procesamiento analítico.
- **QA-09:** Evitar que las consultas analíticas pesadas afecten el rendimiento del panel.
- **CON-03:** Documentación mediante ADRs y definición de contratos.
- **CRN-02:** Separación de las cargas transaccionales y analíticas.

## Alternativas consideradas

### Opción 1: Base de datos compartida OLTP

Utilizar la misma base de datos para las operaciones del panel y las consultas analíticas.

**Ventajas:**
- Arquitectura sencilla.
- No requiere duplicación de datos.
- Acceso a información transaccional actualizada.

**Desventajas:**
- Competencia por recursos entre consultas operativas y analíticas.
- Riesgo de degradación del rendimiento del panel.
- Menor independencia para escalar las cargas de trabajo.

### Opción 2: Réplica de lectura de la base transaccional

Mantener una réplica de la base OLTP destinada exclusivamente a consultas analíticas.

**Ventajas:**
- Reduce la competencia por consultas de lectura en la base principal.
- Permite reutilizar el modelo de datos existente.
- Menor complejidad que incorporar un pipeline analítico completo.

**Desventajas:**
- El modelo transaccional no está optimizado para consultas analíticas complejas.
- La réplica puede experimentar retrasos de sincronización.
- Mantiene dependencia de la estructura de datos operativa.

### Opción 3: Separación OLTP/OLAP mediante CDC

Utilizar Change Data Capture para capturar cambios de la base transaccional y transferirlos mediante un pipeline hacia un almacén analítico independiente.

**Ventajas:**
- Separa las consultas analíticas de las operaciones transaccionales.
- Permite utilizar un modelo de datos optimizado para análisis.
- Facilita la transformación y anonimización de información.
- Permite escalar el procesamiento analítico de manera independiente.

**Desventajas:**
- Requiere componentes adicionales de extracción y transformación.
- Introduce consistencia eventual entre OLTP y OLAP.
- Necesita gestionar errores de sincronización y procesamiento.
- El mecanismo CDC también consume recursos de la infraestructura transaccional.

## Comparación de alternativas

| Criterio | OLTP compartida | Réplica de lectura | CDC + OLAP |
|---|---|---|---|
| Separación de consultas | Nula | Parcial | Alta |
| Complejidad arquitectónica | Baja | Media | Alta |
| Optimización analítica | Limitada | Limitada | Alta |
| Actualización de datos | Inmediata | Eventual | Eventual |
| Escalabilidad independiente | Baja | Parcial | Alta |
| Transformación y anonimización | Requiere mecanismos adicionales | Requiere mecanismos adicionales | Integrable al pipeline |

## Decisión

Se adopta una **arquitectura de datos separada en entornos OLTP y OLAP, utilizando CDC basado en logs transaccionales** para capturar los cambios de la base operativa.

El flujo propuesto es el siguiente:

1. La base OLTP almacena las operaciones habituales de reservas e itinerarios.
2. Un agente CDC captura los cambios registrados en el log transaccional.
3. Los cambios se publican en el Event Broker definido en el ADR-003.
4. Un proceso de transformación valida, filtra y anonimiza la información personal.
5. Los datos procesados se almacenan en un Data Warehouse columnar, destinado a consultas analíticas.
6. Una API de analítica y reportes permite consultar la información agregada.

Se selecciona esta alternativa porque ofrece una separación más adecuada entre las cargas operativas y analíticas, permitiendo optimizar cada entorno según sus necesidades.

La decisión prioriza el rendimiento y la escalabilidad frente a la menor complejidad de las alternativas basadas en una base compartida o una réplica de lectura.

## Consecuencias

### Positivas
- Las consultas analíticas dejan de ejecutarse directamente sobre la base transaccional.
- Mayor independencia para dimensionar las cargas operativas y analíticas.
- Posibilidad de optimizar el almacenamiento para consultas históricas y agregaciones.
- Incorporación de una etapa específica de anonimización de datos personales.

### Negativas
- Mayor complejidad de infraestructura y mantenimiento.
- Duplicación de información entre entornos.
- Consistencia eventual entre los datos operativos y analíticos.
- Necesidad de monitorear el pipeline y gestionar fallas de sincronización.

## Validación de la decisión

La decisión deberá evaluarse considerando los siguientes aspectos:

- **Rendimiento:** verificar que las consultas analíticas no se ejecuten sobre la base OLTP y estimar la sobrecarga introducida por CDC.
- **Escalabilidad:** analizar la posibilidad de aumentar independientemente los recursos de procesamiento analítico.
- **Consistencia:** contemplar retrasos entre los cambios transaccionales y su disponibilidad en OLAP.
- **Privacidad:** comprobar que la transformación elimine o anonimice los datos personales que no sean necesarios para el análisis.
- **Trazabilidad:** verificar la correspondencia entre los cambios capturados, los datos transformados y la información almacenada.

**Estado de validación:** Pendiente de evaluación mediante el diseño arquitectónico o el prototipo académico. La separación de cargas no implica aislamiento absoluto ni garantiza por sí sola el cumplimiento de los atributos de calidad.
