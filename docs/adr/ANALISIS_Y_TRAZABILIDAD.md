# Análisis y trazabilidad del prototipo

## Fuente y criterio
La matriz toma como fuente las páginas 1–3 del TPE de Diseño de Sistemas de Software. La elección de Python, FastAPI y SQLite se registra en el ADR-001 local.

## Alcance del prototipo

Una aplicación FastAPI sirve la interfaz y la API. SQLite conserva los datos del usuario y otro archivo SQLite contiene los eventos analíticos. El correo entra como JSON ya estructurado. La identidad se verifica con tokens de demostración. El proveedor y la derivación a agencias se simulan localmente.

Los números ADR de esta tabla corresponden a los documentos locales del prototipo. La correspondencia con QA-01 a QA-10, CRN, CON y los ADR de la arquitectura objetivo requiere las fichas oficiales de la Wiki. RF y RNF conservan la numeración de este documento, derivada del PDF.

## Matriz de trazabilidad

| Requisito | Decisión arquitectónica | Archivo / endpoint | Prueba | Estado |
|---|---|---|---|---|
| RF-01 · Gestión manual de reservas, p. 2 | ADR-001 y ADR-004 locales. REST y control de propiedad | `app/main.py`, `POST /reservations`, `PATCH/DELETE /reservations/{reservation_id}` | `test_crud_and_user_isolation`, `test_dates_and_null_validations`, `test_reservation_ingestion_and_analytics_contracts` | Implementado. Lectura anidada en viajes |
| RF-02 · Sondeo, escaneo e importación de correo, p. 2 | ADR-003 local. Entrada simulada con deduplicación persistida | `app/main.py`, `POST /email/ingest`. `app/db.py`, `processed_messages` | `test_whitelist_ingestion_and_idempotency`, `test_reservation_ingestion_and_analytics_contracts` | Importación local probada. Sondeo y escaneo fuera de alcance |
| RF-03 · Filtros y lista de remitentes, p. 2 | ADR-003 y ADR-004 locales. Whitelist por usuario | `app/main.py`, `POST/GET /whitelist`, `DELETE /whitelist/{entry_id}` | `test_whitelist_ingestion_and_idempotency` | Alta y filtro probados. Listado y baja implementados |
| RF-04 · Detalles, actualizaciones y cancelaciones de proveedor, p. 2 | ADR-003 local. Proveedor simulado | `app/main.py`, `POST /provider/reservations/{reservation_id}/update` | `test_provider_adapter_and_analytics`, `test_analytics_counts_provider_cancellation_transitions` | Actualización y cancelación simuladas y probadas |
| RF-05 · Agrupación y ciclo de vida del viaje, p. 2 | ADR-001 y ADR-004 locales. Archivado del usuario al consultar el listado activo | `app/main.py`, `GET /trips`, `POST /trips/archive-finished`. `app/services.py`, `archive_finished_trips()` | `test_finished_trip_archiving`, `test_archiving_is_scoped_to_the_authenticated_user`, `test_active_listing_archives_overdue_trips_on_demand` | Implementado bajo demanda. Sin tarea periódica |
| RF-06 · Integración con agencia preferida, p. 2 | ADR-003 local. Se registra la derivación y la agencia indicada | `app/main.py`, `POST /support` | `test_support_bot_and_agency_escalation`, `test_support_answers_only_for_owned_reservations` | Derivación simulada y probada |
| RF-07 · Tendencias, destinos y cancelaciones, p. 2 | ADR-002 local. SQLite separado y escritura posterior al commit operativo | `app/services.py`, `log_analytics()`. `app/main.py`, `GET /analytics/summary` | `test_analytics_counts_provider_cancellation_transitions`, `test_analytics_failure_preserves_operational_write`, `test_reservation_ingestion_and_analytics_contracts` | Agregados por fecha UTC, destino y tipo. Conteo de nuevas transiciones a cancelada por proveedor |
| RF-08 · Opción B, soporte de primer nivel, p. 2 | ADR-003 local. Reglas deterministas y autorización por propiedad para la consulta | `app/services.py`, `classify_support()`. `app/main.py`, `POST /support` | `test_support_answers_only_for_owned_reservations` | Resuelve consulta de estado por ID. Registra y deriva casos complejos de forma simulada |
| RNF-01 · Actualización externa visible dentro de 5 min, pp. 2–3 | ADR-003 local. Solo tramo de actualización local | `app/main.py`, `provider_update()` | `test_provider_adapter_and_analytics` | Flujo simulado. Umbral sin medir |
| RNF-02 · Respuesta web de 800 ms, p. 3 | ADR-001 local. API y UI en un proceso | `app/main.py`, `GET /` y `GET /trips` | Sin prueba de latencia | Sin medir |
| RNF-03 · FCP móvil menor de 1,4 s, p. 3 | UI adaptable. Sin ADR local específico | `app/main.py`, `home()` | `test_home_explains_technical_docs_and_trip_display`, solo HTML | Sin medir |
| RNF-04 · Hasta 5 minutos de caída no planificada al mes, p. 3 | Despliegue local para demostración | `app/main.py`, `GET /health` | `test_health_and_auth`, respuesta puntual | Disponibilidad mensual sin medir |
| RNF-05 · 15 M de cuentas, 2 M activos semanales y picos, pp. 2–3 | ADR-001 local. Persistencia acotada a la demo | `app/db.py`, `connect()` | Sin prueba de carga | Sin medir |
| RNF-06 · Seguridad de correo y acceso restringido a itinerarios, p. 3 | ADR-004 local. Identidad de demo y propiedad | `app/security.py`, `current_user()`. `app/main.py`, consultas por propietario | `test_crud_and_user_isolation`, `test_archiving_is_scoped_to_the_authenticated_user`, `test_support_answers_only_for_owned_reservations` | Propiedad en los casos probados. Correo real y compartición fuera de alcance |
| RNF-07 · Interoperabilidad y evolución, p. 3 | ADR-001 y ADR-003 locales. Contratos OpenAPI y entradas simuladas | `app/main.py`, modelos de reserva, ingesta y analítica | `test_openapi_endpoints_are_grouped_and_described_in_spanish`, `test_reservation_ingestion_and_analytics_contracts` | Contratos locales probados. Integraciones reales fuera de alcance |
| RNF-08 · Usabilidad, internacionalización, GPS y multirregión, p. 3 | UI adaptable en español. Sin ADR local específico | `app/main.py`, `home()` | `test_home_explains_technical_docs_and_trip_display` | Interfaz básica. GPS, i18n y multirregión fuera de alcance |

## Alcance de la evidencia

El resumen analítico consulta `analytics.db`. La escritura comparte proceso con la API, ocurre después del commit operativo y no se reintenta si falla. Los eventos históricos de proveedor carecen del estado necesario para reconstruir las cancelaciones anteriores al cambio.

Se eligió la opción B porque permite verificar con reglas simples la consulta de estado y la derivación simulada de casos complejos.

## Validación manual sugerida
1. Crear un viaje y una reserva desde la interfaz o Swagger.
2. Intentar importar un correo sin whitelist: debe rechazarse.
3. Agregar el remitente a whitelist e importar otro mensaje: debe crear una reserva.
4. Repetir el mismo `message_id`: debe responder `duplicate`.
5. Consultar `/analytics/summary` y anotar `cancellations`.
6. Cancelar una reserva confirmada desde el endpoint simulado de proveedor. Verificar su estado, volver a consultar el resumen y comprobar que `cancellations` aumenta en uno. Revisar `events_by_date`.
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
