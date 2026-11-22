# Análisis y trazabilidad del prototipo

## Fuente y criterio
La matriz toma como fuente las páginas 1–3 del TPE de Diseño de Sistemas de Software. La elección de Python, FastAPI y SQLite se registra en el ADR-P01 local.

## Alcance del prototipo

Una aplicación FastAPI sirve la interfaz y la API. SQLite conserva los datos del usuario y otro archivo SQLite contiene los eventos analíticos. El correo entra como JSON ya estructurado. La identidad se verifica con tokens de demostración. El proveedor y la derivación a agencias se simulan localmente.

Los identificadores ADR-P01 a ADR-P04 corresponden a decisiones de implementación local; ADR-001 a ADR-008 corresponden a la arquitectura objetivo documentada mediante ADD 3.0. La tabla identifica ambos niveles y no implica que el prototipo implemente los componentes productivos propuestos. RF y RNF conservan la numeración interna derivada de la consigna, mientras UC, QA, CON y CRN siguen la identificación de la introducción y las iteraciones ADD.

## Matriz de trazabilidad

| Requisito (RF/RNF) | ADD: UC / QA e iteración | ADR arquitectura objetivo | ADR local / decisión de prototipo | Archivo / endpoint | Prueba | Estado |
|---|---|---|---|---|---|---|
| RF-01 · Gestión manual de reservas, p. 2 | UC-02 · Iter. 1; CON-03; QA-07 (autorización) | ADR-001 (estructura), ADR-002 (Gateway conceptual) | [ADR-P01](./ADR-P01-framework.md) y [ADR-P04](./ADR-P04-autenticacion-isolamiento.md) locales. REST y control de propiedad | `app/main.py`, `POST /reservations`, `PATCH/DELETE /reservations/{reservation_id}` | `test_crud_and_user_isolation`, `test_dates_and_null_validations`, `test_reservation_ingestion_and_analytics_contracts` | Implementado. Lectura anidada en viajes |
| RF-02 · Sondeo, escaneo e importación de correo, p. 2 | UC-01 · Iter. 1; QA-01, QA-08; CON-02/03 | ADR-003 (RabbitMQ objetivo); ADR-005 (adaptadores objetivo) | [ADR-P03](./ADR-P03-integraciones-simuladas.md) local. Entrada simulada con deduplicación persistida | `app/main.py`, `POST /email/ingest`. `app/db.py`, `processed_messages` | `test_whitelist_ingestion_and_idempotency`, `test_previously_recorded_rejected_message_can_be_imported`, `test_reservation_ingestion_and_analytics_contracts` | Rechazo sin consumir ID; reintento permitido al autorizar remitente, incluso con rechazos históricos; duplicados de importaciones exitosas bloqueados. Sondeo y escaneo fuera de alcance |
| RF-03 · Filtros y lista de remitentes, p. 2 | UC-01 · Iter. 1 y 3; QA-07; CRN-04; CON-02 | ADR-005 (adaptadores) | [ADR-P03](./ADR-P03-integraciones-simuladas.md) y [ADR-P04](./ADR-P04-autenticacion-isolamiento.md) locales. Whitelist por usuario | `app/main.py`, `POST/GET /whitelist`, `DELETE /whitelist/{entry_id}` | `test_whitelist_ingestion_and_idempotency` | Alta y filtro probados. Listado y baja implementados |
| RF-04 · Detalles, actualizaciones y cancelaciones de proveedor, p. 2 | UC-01 · Iter. 1 y 3; QA-01, QA-08; CRN-03 | ADR-003 (mensajería), ADR-005 (ACL), ADR-006 (resiliencia) | [ADR-P03](./ADR-P03-integraciones-simuladas.md) local. Proveedor simulado | `app/main.py`, `POST /provider/reservations/{reservation_id}/update` | `test_provider_adapter_and_analytics`, `test_analytics_counts_provider_cancellation_transitions` | Actualización y cancelación simuladas y probadas |
| RF-05 · Agrupación y ciclo de vida del viaje, p. 2 | UC-03 (ciclo de vida) · Iter. 1; QA-07; CON-03 | ADR-001 (estructura) | [ADR-P01](./ADR-P01-framework.md) y [ADR-P04](./ADR-P04-autenticacion-isolamiento.md) locales. Archivado del usuario al consultar el listado activo | `app/main.py`, `GET /trips`, `POST /trips/archive-finished`. `app/services.py`, `archive_finished_trips()` | `test_finished_trip_archiving`, `test_archiving_is_scoped_to_the_authenticated_user`, `test_active_listing_archives_overdue_trips_on_demand` | Implementado bajo demanda. Sin tarea periódica |
| RF-06 · Integración con agencia preferida, p. 2 | UC-04 · Iter. 3 y 5; QA-07, QA-08; CRN-03/04 | ADR-005 (ACL), ADR-006 (resiliencia) | [ADR-P03](./ADR-P03-integraciones-simuladas.md) local. Se registra la derivación y la agencia indicada | `app/main.py`, `POST /support` | `test_support_bot_and_agency_escalation`, `test_support_answers_only_for_owned_reservations` | Derivación simulada y probada |
| RF-07 · Tendencias, destinos y cancelaciones, p. 2 | UC-05 · Iter. 2; QA-06, QA-09; CRN-02; CON-03 | ADR-004 (OLTP/OLAP/CDC objetivo) | [ADR-P02](./ADR-P02-analitica-separada.md) local. SQLite separado y escritura posterior al commit operativo | `app/services.py`, `log_analytics()`. `app/main.py`, `GET /analytics/summary` | `test_analytics_counts_provider_cancellation_transitions`, `test_analytics_counts_manual_and_provider_cancellation_transitions`, `test_analytics_failure_preserves_operational_write`, `test_reservation_ingestion_and_analytics_contracts` | Agregados por fecha UTC, destino y tipo. `cancellations` cuenta transiciones a cancelada por CRUD manual y proveedor, sin duplicar actualizaciones repetidas |
| RF-08 · Opción B, soporte de primer nivel, p. 2 | UC-06, UC-04 · Iter. 5; QA-07, QA-08; CRN-03/04; CON-03 | ADR-005/006 (integración B2B); [ADR-009](./ADR-009-asistente-virtual.md) (asistente por reglas) | [ADR-P03](./ADR-P03-integraciones-simuladas.md) local. Reglas deterministas y autorización por propiedad para la consulta | `app/services.py`, `classify_support()`. `app/main.py`, `POST /support` | `test_support_answers_only_for_owned_reservations`, `test_support_reprogramming_is_escalated_without_modifying_reservation` | Resuelve consulta de estado por ID. Deriva casos complejos y solicitudes de reprogramación de forma simulada, sin modificar reservas |
| RNF-01 · Actualización externa visible dentro de 5 min, pp. 2–3 | QA-01 · Iter. 1; CON-02; umbral de 5 minutos | ADR-003 (mensajería), ADR-005 (adaptadores) | [ADR-P03](./ADR-P03-integraciones-simuladas.md) local. Solo tramo de actualización local | `app/main.py`, `provider_update()` | `test_provider_adapter_and_analytics` | Flujo simulado. Umbral sin medir |
| RNF-02 · Respuesta web de 800 ms, p. 3 | QA-02 · Iter. 1, 3 y 4; Respuesta web menor de 800 ms | ADR-001, ADR-002, ADR-007/008 | [ADR-P01](./ADR-P01-framework.md) local. API y UI en un proceso | `app/main.py`, `GET /` y `GET /trips` | Sin prueba de latencia | Sin medir |
| RNF-03 · FCP móvil menor de 1,4 s, p. 3 | QA-03 · Iter. 4; FCP menor de 1,4 s | ADR-007 (CDN/GLB), ADR-008 (Mobile BFF) | UI adaptable. Sin ADR local específico | `app/main.py`, `home()` | `test_home_explains_technical_docs_and_trip_display`, solo HTML | Sin medir |
| RNF-04 · Hasta 5 minutos de caída no planificada al mes, p. 3 | QA-04 · Iter. 1, 3 y 5; Disponibilidad objetivo de 99,99 % | ADR-001, ADR-006, ADR-007 | Despliegue local para demostración | `app/main.py`, `GET /health` | `test_health_and_auth`, respuesta puntual | Disponibilidad mensual sin medir |
| RNF-05 · 15 M de cuentas, 2 M activos semanales y picos, pp. 2–3 | QA-05 · Iter. 1 y 2; 15 M de cuentas y 2 M activos/semana | ADR-001, ADR-003, ADR-004 | [ADR-P01](./ADR-P01-framework.md) local. Persistencia acotada a la demo | `app/db.py`, `connect()` | Sin prueba de carga | Sin medir |
| RNF-06 · Seguridad de correo y acceso restringido a itinerarios, p. 3 | QA-06/07 · Iter. 2, 3 y 5; CRN-04; autenticación demo, sin compartición | ADR-004 (minimización analítica), ADR-005 (frontera B2B) | [ADR-P04](./ADR-P04-autenticacion-isolamiento.md) local. Identidad de demo y propiedad | `app/security.py`, `current_user()`. `app/main.py`, consultas por propietario | `test_crud_and_user_isolation`, `test_archiving_is_scoped_to_the_authenticated_user`, `test_support_answers_only_for_owned_reservations` | Propiedad en los casos probados. Correo real y compartición fuera de alcance |
| RNF-07 · Interoperabilidad y evolución, p. 3 | QA-08 · Iter. 3; CON-02/03; CRN-03 | ADR-005, ADR-006 | [ADR-P01](./ADR-P01-framework.md) y [ADR-P03](./ADR-P03-integraciones-simuladas.md) locales. Contratos OpenAPI y entradas simuladas | `app/main.py`, modelos de reserva, ingesta y analítica | `test_openapi_endpoints_are_grouped_and_described_in_spanish`, `test_reservation_ingestion_and_analytics_contracts` | Contratos locales probados. Integraciones reales fuera de alcance |
| RNF-08 · Usabilidad, internacionalización, GPS y multirregión, p. 3 | QA-10 y QA-03 · Iter. 4; La usabilidad/GPS/i18n no tienen QA exclusivo en la lista ADD | ADR-007, ADR-008 | UI adaptable en español. Sin ADR local específico | `app/main.py`, `home()` | `test_home_explains_technical_docs_and_trip_display` | Interfaz básica. GPS, i18n y multirregión fuera de alcance |

## Correspondencia y límites entre diseño e implementación

- **Iteración 1:** la arquitectura objetivo define microservicios, API Gateway y RabbitMQ (ADR-001/002/003); la implementación local utiliza una única aplicación FastAPI, REST y simulaciones (ADR-P01/P03). No se implementaron broker ni microservicios distribuidos.
- **Iteración 2:** el diseño separa OLTP/OLAP mediante CDC y un almacén analítico (ADR-004); el prototipo separa dos archivos SQLite y registra eventos síncronamente después del commit operativo (ADR-P02). No hay CDC, Debezium ni ClickHouse real.
- **Iteración 3:** el diseño propone ACL, adaptadores, Circuit Breaker y autorización externa (ADR-005/006); el prototipo normaliza entradas simuladas y usa tokens fijos de demo (ADR-P03/P04). No implementa OAuth2/OIDC, Circuit Breaker ni conexión B2B real.
- **Iteración 4:** se proponen Mobile BFF, CDN, GLB y despliegue multirregión (ADR-007/008). La interfaz del prototipo es web adaptable; no es una aplicación móvil desplegada ni valida estas tácticas de infraestructura.
- **Iteración 5:** el diseño incorpora la opción B, asistente virtual determinista y derivación a agencia, reutilizando conceptualmente la integración B2B (ADR-005/006). El ADR-009 documenta la decisión del asistente por reglas en la arquitectura objetivo. El prototipo consulta estados de reservas propias por ID y registra derivaciones simuladas (ADR-P03/P04); clasifica solicitudes de reprogramación para derivación simulada, pero no ejecuta cambios reales de reservas.

**Convención de UC-03:** UC-03 identifica únicamente la agrupación y el ciclo de vida de viajes, según la introducción y la Iteración 1. La visualización móvil de la Iteración 4 es un refinamiento de la consulta y gestión del itinerario (UC-02/UC-03), no un caso de uso adicional ni una redefinición de UC-03.

**Evidencia:** las pruebas indicadas son funciones presentes en `tests/test_prototype.py`. Su existencia no constituye una medición de latencia, escalabilidad, disponibilidad ni una verificación independiente de ejecución.

## Alcance de la evidencia

El resumen analítico consulta `analytics.db`. La escritura comparte proceso con la API, ocurre después del commit operativo y no se reintenta si falla. El indicador `cancellations` suma eventos `manual_cancelled` y `provider_cancelled` registrados desde este cambio: mide transiciones a cancelada (no cantidad de reservas únicas), excluye reservas creadas inicialmente canceladas y no reconstruye cancelaciones históricas previas. Las escrituras analíticas siguen siendo de mejor esfuerzo.

Se eligió la opción B porque permite verificar con reglas simples la consulta de estado y la derivación simulada de casos complejos.

## Validación manual sugerida
1. Crear un viaje y una reserva desde la interfaz o Swagger.
2. Intentar importar un correo sin whitelist: debe rechazarse.
3. Agregar el remitente a whitelist y reintentar **el mismo `message_id`** rechazado: debe crear una reserva. Repetirlo tras la importación debe devolver `duplicate`.
4. Repetir el mismo `message_id`: debe responder `duplicate`.
5. Consultar `/analytics/summary` y anotar `cancellations`.
6. Cancelar una reserva confirmada desde el endpoint simulado de proveedor y otra mediante `PATCH /reservations/{reservation_id}`. Comprobar que `cancellations` aumenta una vez por cada transición, pero no por repetir una cancelación. Revisar `events_by_date`.
7. Consultar el estado de una reserva propia por ID y verificar la respuesta. Enviar «Necesito un reembolso urgente» para verificar la derivación simulada.
8. Crear un viaje con fecha de fin pasada y consultar `GET /trips`. Verificar que el viaje se archiva a demanda y figura como archivado con `include_archived=true`.
9. Usar el token de Bob para consultar/modificar datos de Alice: no debe acceder a ellos.

## Evidencias para la entrega
- Capturas de `/docs` y de la UI.
- Salida de `python -m pytest -q`.
- Solicitudes y respuestas de ingesta aceptada, rechazada y duplicada.
- Consulta de analítica y evidencia de que usa la base separada.
- Captura de la derivación a la agencia.
- Medición de rendimiento local identificada como prueba exploratoria, no como garantía de SLA.
- ADR/MADR y vistas arquitectónicas que expliquen estas decisiones.
