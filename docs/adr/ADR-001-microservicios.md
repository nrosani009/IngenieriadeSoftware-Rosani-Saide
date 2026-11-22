# ADR-001: Adopción de una arquitectura de microservicios

**Estado:** Aceptada  
**Fecha:** Pendiente de registrar
**Última actualización:** 2026-11-22  
**Iteración ADD:** 1 — Definición de la estructura macro y arquitectura de referencia.

## Contexto y problema

Trotamundos es una plataforma de gestión de viajes que centraliza reservas provenientes de correos electrónicos, proveedores externos y operaciones manuales realizadas por los usuarios.

El sistema debe soportar 15 millones de cuentas registradas, 2 millones de usuarios activos semanales y picos de demanda asociados a contingencias de viaje.

Además, debe permitir la evolución independiente de sus funcionalidades, manteniendo un tiempo de respuesta web inferior a 800 ms y una disponibilidad mensual objetivo del 99,99 %.

Se necesita definir una estructura arquitectónica que permita organizar las responsabilidades del sistema, gestionar cargas de trabajo diferentes y facilitar su crecimiento.

## Drivers arquitectónicos

- **UC-01:** Importación y centralización automática de reservas.
- **UC-02:** Gestión manual de reservas.
- **QA-02:** Tiempo de respuesta web inferior a 800 ms.
- **QA-04:** Disponibilidad mensual del 99,99 %.
- **QA-05:** Soporte de 15 millones de cuentas y 2 millones de usuarios activos semanales.
- **CRN-01:** Definición de la estructura arquitectónica inicial.

## Alternativas consideradas

### Opción 1: Arquitectura monolítica modular

Implementar las funcionalidades dentro de una única aplicación desplegable, organizada internamente en módulos con responsabilidades diferenciadas.

**Ventajas:**
- Menor complejidad inicial de desarrollo y despliegue.
- Comunicación interna directa, sin sobrecarga de red entre módulos.
- Mayor simplicidad para gestionar transacciones y depurar errores.

**Desventajas:**
- Menor granularidad para escalar funcionalidades específicas.
- Los despliegues afectan a la aplicación completa.
- Una falla grave del proceso puede comprometer todas las funcionalidades.

### Opción 2: Arquitectura de microservicios

Dividir el sistema en servicios independientes, organizados según sus responsabilidades funcionales y comunicados mediante interfaces definidas.

**Ventajas:**
- Permite escalar servicios según sus necesidades particulares.
- Facilita despliegues y modificaciones independientes.
- Favorece la separación de responsabilidades y la evolución funcional.
- Permite aplicar mecanismos de resiliencia específicos por servicio.

**Desventajas:**
- Mayor complejidad operativa y de infraestructura.
- Requiere gestionar comunicación distribuida y fallas de red.
- Introduce desafíos de observabilidad y consistencia de datos.
- Puede incrementar la latencia por comunicaciones entre servicios.

## Comparación de alternativas

| Criterio | Monolito modular | Microservicios |
|---|---|---|
| Complejidad inicial | Baja | Alta |
| Escalabilidad independiente | Limitada | Alta |
| Despliegue independiente | No | Sí |
| Comunicación interna | Directa | Distribuida |
| Aislamiento de fallas | Limitado | Potencialmente mayor |
| Mantenimiento operativo | Más sencillo | Más complejo |
| Evolución funcional | Modular, pero con despliegue conjunto | Independiente por servicio |

## Decisión

Se adopta una **arquitectura de microservicios**, separando las responsabilidades principales de Trotamundos en servicios especializados.

La decisión se fundamenta en la necesidad de gestionar cargas heterogéneas, permitir el escalado independiente y facilitar la incorporación de nuevas funcionalidades e integraciones externas.

Se priorizan estas capacidades frente a la menor complejidad inicial que ofrece una arquitectura monolítica modular.

La arquitectura contempla inicialmente servicios responsables de la ingesta, integración y ciclo de vida de reservas, y gestión de reservas, manteniendo interfaces explícitas entre ellos.

Los mecanismos concretos de mensajería, persistencia y comunicación serán documentados mediante ADRs independientes.

## Consecuencias

### Positivas
- Posibilidad de escalar componentes de acuerdo con su demanda.
- Mayor independencia para desarrollar y desplegar funcionalidades.
- Separación explícita de responsabilidades.
- Flexibilidad para incorporar nuevas integraciones y capacidades.

### Negativas
- Mayor complejidad de despliegue, configuración y monitoreo.
- Necesidad de gestionar errores de comunicación entre servicios.
- Mayor esfuerzo para garantizar la consistencia de datos.
- Costos adicionales de infraestructura y operación.

## Validación de la decisión

La elección de microservicios no garantiza por sí misma el cumplimiento de los atributos de calidad.

Se deberán realizar pruebas y evaluaciones para verificar:

- **Rendimiento:** tiempo de respuesta web inferior a 800 ms bajo una carga representativa.
- **Escalabilidad:** comportamiento del sistema frente a aumentos de concurrencia y picos de demanda.
- **Disponibilidad:** recuperación ante fallas y cumplimiento del presupuesto mensual de indisponibilidad.
- **Mantenibilidad:** capacidad de modificar y desplegar un servicio sin requerir el redespliegue de los demás.

**Estado de validación:** Pendiente de pruebas mediante el prototipo y evaluaciones arquitectónicas.
