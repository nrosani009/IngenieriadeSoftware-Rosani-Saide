# ADR-002: Adopción de API Gateway

**Estado:** Aceptada  
**Fecha:** Pendiente de registrar
**Última actualización:** 2026-11-22  
**Iteración ADD:** 1 — Definición de la estructura macro y arquitectura de referencia.

## Contexto y problema

Trotamundos debe ofrecer acceso a sus funcionalidades desde una aplicación web y una aplicación móvil. Ambas necesitan comunicarse con los servicios internos encargados de gestionar reservas, itinerarios e integraciones externas.

Al adoptar una arquitectura de microservicios (ADR-001), surge la necesidad de definir cómo los clientes accederán a estos servicios sin depender directamente de su ubicación o estructura interna.

Además, el sistema debe contemplar mecanismos de seguridad, control de acceso y enrutamiento de solicitudes.

## Drivers arquitectónicos

- **UC-02:** Gestión manual de reservas desde el panel.
- **QA-02:** Tiempo de respuesta web inferior a 800 ms.
- **QA-04:** Disponibilidad global del 99,99 % mensual.
- **CON-01:** Despliegue sobre infraestructura de nube pública.
- **CON-03:** Uso de contratos de API mediante Spec-Driven Development.

## Alternativas consideradas

### Opción 1: Acceso directo a los microservicios

Los clientes web y móvil se comunican directamente con cada servicio mediante sus respectivas APIs.

**Ventajas:**
- Menor cantidad de componentes intermedios.
- No incorpora la latencia adicional de un Gateway.
- Implementación inicial sencilla para pocos servicios.

**Desventajas:**
- Los clientes deben conocer las direcciones de múltiples servicios.
- Mayor acoplamiento entre clientes y estructura interna.
- Las políticas de acceso y seguridad deben coordinarse entre múltiples puntos de entrada.

### Opción 2: API Gateway centralizado

Se incorpora un componente que actúa como punto de entrada para las solicitudes provenientes de los clientes y las enruta hacia los servicios correspondientes.

**Ventajas:**
- Centraliza el enrutamiento y las políticas comunes de acceso.
- Oculta la estructura interna de los microservicios.
- Facilita la evolución de los servicios sin modificar necesariamente los clientes.
- Permite incorporar controles transversales, como limitación de solicitudes y registro de accesos.

**Desventajas:**
- Introduce un componente adicional.
- Puede convertirse en un cuello de botella.
- Requiere contemplar su disponibilidad y escalabilidad.
- Agrega una etapa de procesamiento a las solicitudes.

## Comparación de alternativas

| Criterio | Acceso directo | API Gateway |
|---|---|---|
| Acoplamiento cliente-servicios | Alto | Menor |
| Centralización del acceso | No | Sí |
| Complejidad inicial | Baja | Media |
| Políticas de seguridad comunes | Distribuidas | Centralizables |
| Evolución de servicios internos | Mayor impacto en clientes | Menor impacto potencial |
| Latencia adicional | Menor | Introduce un salto adicional |
| Dependencia de un punto de entrada | Distribuida | Concentrada en el Gateway |

## Decisión

Se adopta un **API Gateway como punto de entrada lógico** para las aplicaciones web y móvil de Trotamundos.

El Gateway será responsable de recibir las solicitudes, aplicar controles comunes de acceso y dirigirlas hacia los servicios internos correspondientes.

La decisión prioriza el desacoplamiento entre clientes y servicios, la centralización de responsabilidades transversales y la facilidad de evolución de la arquitectura.

Se contempla el uso de OAuth 2.0 para el acceso autorizado, sin definir en este ADR el proveedor de identidad ni el mecanismo específico de validación de tokens.

## Consecuencias

### Positivas
- Simplificación de la comunicación entre clientes y servicios.
- Centralización de controles comunes de acceso y enrutamiento.
- Menor exposición de la estructura interna.
- Mayor flexibilidad para reorganizar los servicios.

### Negativas
- Incorporación de un componente adicional a la arquitectura.
- Posible aumento de latencia.
- Necesidad de evitar que el Gateway constituya un punto único de falla.
- Mayor complejidad de configuración y mantenimiento.

## Validación de la decisión

La adopción del API Gateway deberá evaluarse respecto de los siguientes aspectos:

- **Rendimiento:** analizar su contribución al tiempo de respuesta objetivo de 800 ms.
- **Disponibilidad:** contemplar redundancia o mecanismos de recuperación para evitar un punto único de falla.
- **Seguridad:** verificar que las solicitudes protegidas requieran credenciales válidas y que los servicios apliquen las autorizaciones correspondientes.
- **Mantenibilidad:** comprobar que la incorporación o modificación de servicios pueda realizarse con cambios mínimos en los clientes.

**Estado de validación:** Pendiente de evaluación mediante el diseño arquitectónico y, cuando corresponda, el prototipo académico.
