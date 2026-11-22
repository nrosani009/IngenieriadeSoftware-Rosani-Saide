# ADR-008: Optimización del rendimiento móvil mediante Backend for Frontend (BFF)

**Estado:** Aceptada  
**Fecha:** Pendiente de registrar
**Última actualización:** 2026-11-22  
**Iteración ADD:** 4 — Optimización del rendimiento móvil y distribución global.

## Contexto y problema

Trotamundos debe permitir que los usuarios consulten sus reservas e itinerarios desde dispositivos móviles, manteniendo una experiencia de navegación rápida y eficiente.

La aplicación móvil puede necesitar únicamente una parte de la información disponible en los servicios internos. Recuperar itinerarios completos, historiales y atributos innecesarios incrementa el volumen de datos transferidos y puede afectar el tiempo de carga inicial.

La arquitectura debe contemplar un First Contentful Paint (FCP) inferior a 1,4 segundos y un tiempo de respuesta web inferior a 800 ms.

Se necesita definir una estrategia que permita adaptar las respuestas del backend a las necesidades específicas del cliente móvil, reduciendo la transferencia de información innecesaria y favoreciendo el renderizado progresivo.

## Drivers arquitectónicos

- **UC-02 / UC-03 (refinamiento móvil):** Consulta y presentación del itinerario desde la aplicación móvil, vinculadas a la gestión de reservas (UC-02) y al ciclo de vida de viajes (UC-03). La visualización móvil no redefine UC-03 ni constituye un nuevo caso de uso.
- **QA-02:** Tiempo de respuesta web inferior a 800 ms.
- **QA-03:** FCP móvil inferior a 1,4 segundos.
- **QA-10:** Distribución global y reducción de latencia geográfica mediante infraestructura multirregión.
- **CON-01:** Despliegue sobre infraestructura de nube bajo un modelo SaaS.

## Alternativas consideradas

### Opción 1: Consumo directo de microservicios

La aplicación móvil realiza solicitudes directamente a los distintos microservicios para obtener la información necesaria.

**Ventajas:**
- No requiere una capa adicional de adaptación.
- Permite acceder directamente a las funcionalidades de cada servicio.
- Menor complejidad inicial del backend.

**Desventajas:**
- Puede requerir múltiples solicitudes desde el dispositivo.
- Incrementa el acoplamiento entre el cliente y los servicios internos.
- Puede aumentar la latencia acumulada en redes móviles.

### Opción 2: API Gateway con respuestas generales

La aplicación móvil accede a los servicios mediante el API Gateway existente, utilizando las mismas respuestas que la aplicación web.

**Ventajas:**
- Reutiliza la infraestructura definida en el ADR-002.
- Centraliza el acceso y las políticas comunes.
- Evita incorporar un componente específico para dispositivos móviles.

**Desventajas:**
- Las respuestas pueden contener información innecesaria.
- No contempla necesariamente las necesidades particulares del cliente móvil.
- Puede requerir múltiples solicitudes para construir una pantalla.

### Opción 3: Mobile Backend for Frontend (BFF)

Se incorpora una capa especializada que adapta y consolida la información proveniente de los servicios internos antes de enviarla a la aplicación móvil.

**Ventajas:**
- Permite reducir el tamaño de las respuestas mediante Data Trimming.
- Facilita consolidar información de varios servicios.
- Reduce potencialmente la cantidad de solicitudes realizadas por el cliente.
- Permite adaptar las respuestas a las necesidades de la interfaz móvil.

**Desventajas:**
- Introduce un componente adicional.
- Requiere mantener contratos específicos para el cliente móvil.
- Puede duplicar lógica de presentación si no se delimitan correctamente sus responsabilidades.
- Agrega procesamiento en el backend.

## Comparación de alternativas

| Criterio | Acceso directo | API Gateway general | Mobile BFF |
|---|---|---|---|
| Complejidad inicial | Baja | Media | Media/Alta |
| Adaptación al cliente móvil | Limitada | Limitada | Alta |
| Reducción de payload | Depende de cada servicio | Depende de las APIs | Centralizada |
| Consolidación de respuestas | En el cliente | Opcional | Sí |
| Cantidad de solicitudes móviles | Potencialmente alta | Variable | Potencialmente menor |
| Acoplamiento con servicios internos | Alto | Menor | Bajo |
| Mantenimiento | Distribuido entre clientes y servicios | Centralizado parcialmente | Requiere mantener el BFF |

## Decisión

Se adopta un **Mobile Backend for Frontend (BFF)** como capa de adaptación entre el API Gateway y los servicios internos de Trotamundos.

El Mobile BFF será responsable de:

1. **Reducir el payload (Data Trimming):** devolver únicamente los atributos necesarios para la visualización inicial del itinerario, evitando transferir historiales completos o información interna innecesaria.
2. **Consolidar solicitudes:** recuperar información de distintos servicios y construir una respuesta adaptada al cliente móvil.
3. **Facilitar la carga progresiva:** permitir que la aplicación solicite inicialmente las reservas correspondientes a los próximos tres días de viaje y recupere el resto bajo demanda.
4. **Mantener contratos específicos:** definir respuestas orientadas a las necesidades de la interfaz móvil, sin modificar los contratos internos de los microservicios.

El API Gateway continuará gestionando el acceso y el enrutamiento, mientras que el Mobile BFF se encargará de adaptar la información solicitada por el cliente.

La decisión se fundamenta en la necesidad de reducir la transferencia de datos y simplificar la construcción de las pantallas móviles, priorizando el rendimiento percibido frente a la menor complejidad de utilizar respuestas generales.

La distribución geográfica de solicitudes y recursos estáticos se mantiene como una decisión independiente, documentada en el ADR-007.

## Consecuencias

### Positivas

- Reducción potencial del volumen de datos transferidos.
- Menor cantidad de solicitudes necesarias para construir determinadas pantallas.
- Mayor independencia entre la interfaz móvil y los contratos internos.
- Posibilidad de adaptar las respuestas a futuras necesidades de la aplicación.
- Compatibilidad con la estrategia de Lazy Loading definida en la iteración 4.

### Negativas

- Incorporación de una capa adicional de procesamiento.
- Mayor esfuerzo de mantenimiento de contratos y transformaciones.
- Posible duplicación de lógica si no se separan adecuadamente las responsabilidades.
- Necesidad de supervisar la latencia introducida por el BFF.

## Validación de la decisión

Para evaluar la solución propuesta se consideran los siguientes aspectos:

- **Reducción de payload:** comparar el tamaño de una respuesta general con una respuesta adaptada por el Mobile BFF.
- **Cantidad de solicitudes:** analizar cuántas solicitudes necesita el cliente para construir la pantalla inicial con y sin BFF.
- **Rendimiento:** estimar la latencia agregada por la consolidación de datos y su efecto sobre el tiempo total de respuesta.
- **Carga progresiva:** verificar que la aplicación pueda consultar inicialmente los próximos tres días de viaje y solicitar información adicional bajo demanda.
- **Mantenibilidad:** evaluar si pueden modificarse los datos presentados en el cliente móvil sin alterar los contratos internos.

El uso de Mobile BFF y la reducción del payload pueden contribuir a mejorar el rendimiento, pero no garantizan por sí solos un FCP inferior a 1,4 segundos, ya que este depende también del procesamiento del cliente, la descarga de recursos y las condiciones de red.

**Estado de validación:** Pendiente de evaluación mediante estimaciones, comparación de respuestas o pruebas acotadas del prototipo académico.
