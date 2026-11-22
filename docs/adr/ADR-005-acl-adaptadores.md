# ADR-005: Integración con agencias externas mediante Anti-Corruption Layer y adaptadores

**Estado:** Aceptada  
**Fecha:** 2026-11-20 (primer registro verificable en GitHub; no necesariamente fecha de la decisión)
**Última actualización:** 2026-11-22  
**Iteración ADD:** 3 — Diseño del módulo de soporte e integración B2B con agencias de viajes.

## Contexto y problema

Trotamundos debe integrarse con agencias de viajes y proveedores externos para obtener información sobre reservas, actualizaciones y cancelaciones, además de facilitar la resolución de problemas durante los viajes.

Estos sistemas pueden utilizar diferentes estructuras de datos, contratos de API y mecanismos de comunicación. Incorporar directamente estas particularidades al modelo interno de Trotamundos generaría dependencias que dificultarían el mantenimiento y la incorporación de nuevos proveedores.

Se necesita definir una estrategia de integración que permita traducir los formatos externos hacia un modelo común, minimizando el impacto de los cambios realizados por terceros.

## Drivers arquitectónicos

- **UC-04:** Integración con la agencia de viajes preferida para la resolución de problemas.
- **QA-08:** Modificabilidad y extensibilidad para incorporar nuevos proveedores y medios de transporte.
- **CON-02:** Interoperabilidad con APIs heterogéneas de terceros.
- **CON-03:** Definición de contratos de integración mediante Spec-Driven Development.
- **CRN-03:** Aislamiento de dominios y mapeo de modelos externos.

## Alternativas consideradas

### Opción 1: Integración directa con APIs externas

Los servicios internos de Trotamundos consumen directamente las APIs de cada agencia, incorporando la lógica de conversión de datos dentro de los propios servicios de negocio.

**Ventajas:**
- Menor cantidad de componentes.
- Implementación inicial sencilla para pocas integraciones.
- Comunicación directa con los proveedores.

**Desventajas:**
- Alto acoplamiento con los formatos externos.
- Los cambios en las APIs pueden afectar la lógica de negocio.
- Dificulta incorporar nuevos proveedores sin modificar componentes existentes.

### Opción 2: Adaptadores independientes por proveedor

Se implementa un adaptador para cada agencia o proveedor, encargado de gestionar su API y transformar las respuestas a un formato común.

**Ventajas:**
- Encapsula las particularidades de cada proveedor.
- Facilita incorporar nuevas integraciones.
- Permite modificar un adaptador sin afectar necesariamente a los demás.

**Desventajas:**
- Puede producir inconsistencias en las transformaciones.
- No establece por sí sola una política centralizada de protección del modelo de dominio.
- Puede duplicar reglas de validación y normalización.

### Opción 3: Anti-Corruption Layer (ACL) con adaptadores

Se incorpora una capa de integración que actúa como intermediaria entre el dominio interno de Trotamundos y los sistemas externos.

La ACL define un modelo canónico y utiliza adaptadores especializados para comunicarse con cada proveedor.

**Ventajas:**
- Protege el modelo interno frente a estructuras externas heterogéneas.
- Centraliza las reglas de traducción y normalización.
- Facilita incorporar nuevos proveedores mediante interfaces comunes.
- Favorece la mantenibilidad y evolución de las integraciones.

**Desventajas:**
- Introduce una capa arquitectónica adicional.
- Requiere definir y mantener un modelo canónico.
- Aumenta el esfuerzo inicial de diseño.
- Los cambios en el modelo común pueden requerir actualizar varios adaptadores.

## Comparación de alternativas

| Criterio | Integración directa | Adaptadores | ACL + adaptadores |
|---|---|---|---|
| Acoplamiento con APIs externas | Alto | Bajo | Bajo |
| Protección del modelo interno | Baja | Parcial | Alta |
| Incorporación de proveedores | Requiere modificar servicios | Mediante nuevos adaptadores | Mediante adaptadores y contratos comunes |
| Normalización de datos | Distribuida | Por adaptador | Centralizada en la ACL |
| Complejidad inicial | Baja | Media | Alta |
| Mantenibilidad ante cambios externos | Baja | Media/Alta | Alta |

## Decisión

Se adopta una **Anti-Corruption Layer (ACL) combinada con el patrón Adapter/Plugin** para gestionar las integraciones B2B de Trotamundos.

La ACL será responsable de traducir los datos provenientes de las agencias y proveedores hacia el modelo canónico de reservas utilizado internamente.

Cada proveedor contará con un adaptador que implementará una interfaz común, como `IAgencyAdapter` o `ITransportProviderAdapter`, encapsulando sus particularidades técnicas.

Esta alternativa se selecciona porque responde directamente a los requerimientos de interoperabilidad y extensibilidad, reduciendo la dependencia del dominio interno respecto de los contratos externos.

Se prioriza la mantenibilidad frente a la menor complejidad inicial de una integración directa.

Los mecanismos de resiliencia frente a fallas externas se documentarán en un ADR independiente.

## Consecuencias

### Positivas
- Menor acoplamiento entre el dominio interno y las APIs externas.
- Mayor facilidad para incorporar agencias y medios de transporte.
- Centralización de las reglas de traducción y normalización.
- Posibilidad de modificar integraciones sin alterar directamente la lógica de negocio.

### Negativas
- Mayor cantidad de componentes y contratos.
- Necesidad de mantener actualizado el modelo canónico.
- Esfuerzo adicional para desarrollar y probar adaptadores.
- Posible sobrecarga de procesamiento durante la transformación de datos.

## Validación de la decisión

La solución propuesta deberá evaluarse mediante los siguientes aspectos:

- **Modificabilidad:** analizar si es posible incorporar un nuevo proveedor implementando un adaptador sin modificar el modelo de dominio interno.
- **Interoperabilidad:** comprobar que diferentes formatos externos puedan transformarse al modelo canónico.
- **Mantenibilidad:** evaluar el impacto de modificar el contrato de una agencia existente.
- **Rendimiento:** considerar la sobrecarga introducida por las operaciones de traducción.
- **Trazabilidad:** verificar que las interfaces de integración estén documentadas mediante contratos explícitos.

**Estado de validación:** Pendiente de evaluación mediante el diseño arquitectónico o el prototipo académico. La ACL reduce el acoplamiento, pero no elimina completamente las dependencias con los sistemas externos.
