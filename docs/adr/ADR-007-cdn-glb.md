# ADR-007: Distribución global mediante CDN y Global Load Balancer

**Estado:** Aceptada  
**Fecha:** Pendiente de registrar
**Última actualización:** 2026-11-22  
**Iteración ADD:** 4 — Optimización del rendimiento móvil y distribución global.

## Contexto y problema

Trotamundos es una plataforma de gestión de viajes destinada a usuarios distribuidos internacionalmente, que necesitan consultar sus reservas e itinerarios desde aplicaciones web y móviles.

La distancia geográfica entre los usuarios y los servidores puede incrementar la latencia de red, afectando la descarga de recursos estáticos y la respuesta de las solicitudes dinámicas.

La arquitectura debe contemplar un tiempo de respuesta web inferior a 800 ms y un First Contentful Paint (FCP) móvil inferior a 1,4 segundos, además de estar preparada para operar en múltiples regiones.

Se necesita definir una estrategia de distribución que reduzca el impacto de la distancia geográfica y facilite el acceso desde distintas ubicaciones.

## Drivers arquitectónicos

- **UC-03:** Visualización del panel de viajes desde la aplicación móvil.
- **QA-02:** Tiempo de respuesta web inferior a 800 ms.
- **QA-03:** FCP móvil inferior a 1,4 segundos.
- **QA-10:** Distribución global y reducción de latencia geográfica mediante infraestructura multirregión.
- **CON-01:** Despliegue sobre infraestructura de nube bajo un modelo SaaS.

## Alternativas consideradas

### Opción 1: Despliegue centralizado en una única región

Todos los usuarios acceden a los servicios y recursos estáticos alojados en una única región de infraestructura.

**Ventajas:**
- Menor complejidad de despliegue y mantenimiento.
- No requiere coordinación entre regiones.
- Menores costos iniciales de infraestructura.

**Desventajas:**
- Mayor latencia para usuarios geográficamente alejados.
- Dependencia de una única región.
- Menor flexibilidad para distribuir la carga internacional.

### Opción 2: Despliegue multirregión sin distribución perimetral

Los servicios se despliegan en distintas regiones, permitiendo que los usuarios accedan a servidores geográficamente próximos mediante mecanismos de resolución o configuración regional.

**Ventajas:**
- Reduce potencialmente la distancia entre usuarios y servidores.
- Permite distribuir las cargas de procesamiento.
- Mejora las posibilidades de continuidad ante fallas regionales.

**Desventajas:**
- Requiere administrar múltiples despliegues.
- La selección de región puede ser menos adaptable ante fallas.
- Los recursos estáticos continúan dependiendo de los servidores regionales.

### Opción 3: CDN y Global Load Balancer con despliegue multirregión

Se incorpora una Content Delivery Network (CDN) para distribuir recursos estáticos y un Global Load Balancer (GLB) para dirigir las solicitudes dinámicas hacia las regiones disponibles más adecuadas.

**Ventajas:**
- Reduce la distancia de descarga de recursos estáticos mediante caché perimetral.
- Permite seleccionar regiones considerando proximidad y disponibilidad.
- Facilita la distribución geográfica de solicitudes.
- Contribuye a mejorar la experiencia de usuarios internacionales.

**Desventajas:**
- Mayor complejidad de infraestructura.
- Necesidad de gestionar políticas de caché e invalidación.
- Costos adicionales de distribución y transferencia.
- Requiere coordinar el acceso a datos entre regiones.

## Comparación de alternativas

| Criterio | Región única | Multirregión | CDN + GLB |
|---|---|---|---|
| Complejidad inicial | Baja | Alta | Alta |
| Distribución de recursos estáticos | Centralizada | Regional | Perimetral |
| Selección dinámica de región | No | Limitada según implementación | Sí |
| Latencia para usuarios distantes | Potencialmente alta | Menor | Potencialmente menor |
| Tolerancia a fallas regionales | Limitada | Posible | Posible con configuración adecuada |
| Costos de infraestructura | Menores | Mayores | Mayores |

## Decisión

Se adopta una **estrategia de distribución global basada en CDN y Global Load Balancer (GLB)**, sobre una arquitectura preparada para despliegues multirregión.

La solución contempla dos mecanismos complementarios:

1. **CDN / Edge Caching:** distribuye recursos estáticos, como imágenes, iconos y archivos de la interfaz, mediante nodos perimetrales cercanos a los usuarios.
2. **Global Load Balancer:** dirige las solicitudes dinámicas hacia la región disponible más adecuada, considerando criterios de proximidad geográfica y estado de los servicios.

El GLB podrá utilizar información aproximada de ubicación derivada de la dirección IP y verificaciones de disponibilidad. No se requiere acceder al GPS del dispositivo para realizar el enrutamiento.

Esta alternativa se selecciona porque permite abordar tanto la distribución de contenido estático como el acceso regional a los servicios dinámicos, respondiendo a los objetivos de rendimiento e internacionalización.

Se prioriza la reducción de latencia y la flexibilidad de distribución frente a la menor complejidad de un despliegue centralizado.

La optimización de los datos enviados al cliente móvil mediante Mobile BFF se documentará en un ADR independiente.

## Consecuencias

### Positivas

- Menor latencia potencial en la descarga de recursos estáticos.
- Posibilidad de dirigir solicitudes hacia regiones próximas y disponibles.
- Mayor flexibilidad para atender usuarios distribuidos internacionalmente.
- Posibilidad de reducir la carga sobre los servidores de origen mediante caché.

### Negativas

- Mayor complejidad de configuración y despliegue.
- Necesidad de definir políticas de invalidación y actualización de caché.
- Incremento de costos de infraestructura.
- Dependencia de mecanismos de coordinación y acceso a datos entre regiones.

## Validación de la decisión

Para evaluar la solución propuesta se consideran los siguientes aspectos:

- **Rendimiento web:** estimar la contribución de la latencia de red al objetivo de respuesta inferior a 800 ms.
- **Rendimiento móvil:** analizar cómo la distribución de recursos estáticos contribuye al FCP inferior a 1,4 segundos.
- **Distribución geográfica:** verificar conceptualmente que el GLB pueda seleccionar una región adecuada según proximidad y disponibilidad.
- **Disponibilidad:** evaluar el comportamiento del enrutamiento ante la indisponibilidad de una región.
- **Consistencia:** identificar las dependencias de datos que podrían limitar el uso de regiones alternativas.

La CDN y el GLB no garantizan por sí solos los tiempos de respuesta establecidos, ya que estos también dependen del procesamiento interno, la red del usuario y el rendimiento del dispositivo.

**Estado de validación:** Pendiente de evaluación mediante estimaciones de latencia, diagramas de despliegue y, cuando corresponda, pruebas acotadas del prototipo académico.
