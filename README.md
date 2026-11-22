# Trotamundos

## 1. ¿Qué es Trotamundos?

Trotamundos es un prototipo académico del TPE de Diseño de Sistemas de Software. Permite organizar reservas por viaje, consultar su estado con un asistente por reglas y ver cómo se simula la derivación de consultas complejas. La aplicación usa FastAPI y dos bases SQLite locales, una para los datos operativos y otra para los eventos analíticos.

## 2. Requisitos previos

- **Python 3.11 o superior.** La última verificación se hizo con Python 3.13. [Descarga oficial de Python](https://www.python.org/downloads/).
- Un navegador web. Las dependencias de Python se instalan con `pip` en el paso 4.

## 3. Obtener el proyecto

El proyecto ya está disponible en [GitHub](https://github.com/nrosani009/IngenieriadeSoftware-Rosani-Saide). Para descargarlo sin instalar Git:

1. Abrí el repositorio y seleccioná **Code → Download ZIP**.
2. Descomprimí el archivo descargado.
3. Abrí una terminal en la carpeta extraída que contiene `README.md`, `requirements.txt` y `app/`.

También podés usar una carpeta del proyecto entregada por separado. Si ya tenés Git instalado, opcionalmente podés clonarlo:

```bash
git clone https://github.com/nrosani009/IngenieriadeSoftware-Rosani-Saide.git
cd IngenieriadeSoftware-Rosani-Saide
```

**No es necesario instalar Git** si utilizás la descarga ZIP.

## 4. Instalar las dependencias

**Windows (PowerShell)**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Si PowerShell bloquea la activación, instalá con `.\.venv\Scripts\python.exe -m pip install -r requirements.txt`. Para los pasos 5 y 8, reemplazá `python` por `.\.venv\Scripts\python.exe`.

**Linux o macOS**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 5. Ejecutar el prototipo

Desde la misma terminal y en la carpeta del proyecto:

```bash
python -m uvicorn app.main:app --reload
```

Dejá abierta la terminal mientras usás el prototipo. Al iniciar, la aplicación crea las bases SQLite si faltan. Opcionalmente, podés cambiar sus rutas con `TROTAMUNDOS_DB` y `TROTAMUNDOS_ANALYTICS_DB`.

## 6. Acceder desde el navegador

- **Interfaz web:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentación interactiva de la API (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Estado del servidor:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## 7. Probar el recorrido principal

1. Abrí la interfaz. El campo **Token** viene con el de Alice, `demo-alice-token`. Para usar a Bob, cambialo por `demo-bob-token`. Hacé clic en **Cargar viajes** para ver los datos del usuario elegido.
2. En **Crear viaje**, escribí un nombre y hacé clic en **Crear viaje**. El ID se copia al formulario de reservas.
3. Elegí un tipo y un proveedor y hacé clic en **Agregar reserva**. Anotá el número que aparece como **Reserva #…** en la tarjeta del viaje. La interfaz mantiene la selección explícita por ID; en Swagger también podés omitir `trip_id` y proporcionar `start_at` para asociar la reserva automáticamente a un único viaje activo propio cuyas fechas contengan la reserva.
4. En **Soporte**, escribí «¿Cuál es el estado de mi reserva?», ingresá ese ID y hacé clic en **Consultar asistente**.
5. Enviá «Necesito un reembolso urgente» o «Quiero reprogramar mi vuelo» para ver la derivación simulada a la agencia indicada en el formulario. La demo no modifica la reserva al solicitar una reprogramación.

Para probar una operación protegida directamente desde Swagger, ingresá `Bearer demo-alice-token` o `Bearer demo-bob-token` en el campo `authorization`. En la interfaz web, ingresá solo el token, sin el prefijo `Bearer`.

## 8. Ejecutar las pruebas

Desde la carpeta del proyecto, con el entorno virtual activo:

```bash
python -m pytest -q
```

**Validación local (Codex, 22/11/2026):** 22 pruebas ejecutadas, 22 aprobadas y 0 fallidas. Se comprobó también la sintaxis con `python -m compileall -q app tests` y la resolución de referencias OpenAPI. En un entorno Windows, la primera ejecución encontró un problema de permisos al crear la carpeta temporal de `pytest`; se resolvió configurando un directorio temporal accesible, sin modificar el código.

En una medición exploratoria con `TestClient` (40 solicitudes, 12 viajes), `GET /trips` tuvo mediana de 1,49 ms y p95 de 2,05 ms. La traza SQL mostró 2 consultas `SELECT` para recuperar los viajes y sus reservas. **Estos valores no acreditan QA-02 en condiciones reales de red o carga.**

## 9. Finalizar la revisión

1. Volvé a la terminal donde está corriendo Uvicorn y presioná **Ctrl+C**. Esperá a que vuelva el prompt. Esto detiene el servidor y el recargador de `--reload`.
2. Si activaste el entorno virtual, ejecutá `deactivate` en esa terminal. Luego podés cerrarla.

Podés cerrar la pestaña del navegador cuando termines. El servidor se detiene desde la terminal.

## 10. Limitaciones

- La demo funciona en local. No requiere servicios externos ni infraestructura en la nube.
- Las integraciones con correo, proveedores y agencias son simuladas. Los tokens fijos son exclusivos de la demo. Un correo rechazado por remitente no permitido puede reintentarse con el mismo `message_id` una vez autorizado; las importaciones realizadas se deduplican.
- La agrupación automática por fechas solo funciona si existe un único viaje activo propio compatible; si no hay coincidencias o son ambiguas, debe indicarse `trip_id`. No se crean viajes automáticamente.
- El archivado de viajes vencidos ocurre **bajo demanda** al consultar el listado activo (`GET /trips`) o al ejecutar `POST /trips/archive-finished`. `GET /trips?include_archived=true` solo muestra todos los viajes y no dispara el archivado; no se ejecuta ninguna tarea periódica.
- El listado de viajes recupera las reservas en una consulta conjunta (sin una consulta por cada viaje). Esto reduce el número de consultas SQLite, pero no constituye una medición de rendimiento bajo carga.
- La analítica separa almacenamiento y consultas. El indicador `cancellations` cuenta nuevas transiciones a cancelada tanto manuales como del proveedor simulado; no representa reservas únicas canceladas ni recupera eventos históricos. Si falla el registro de un evento, la operación principal puede completarse y el evento puede perderse. El rendimiento, la disponibilidad y la escala de producción quedan fuera de la verificación.

Para consultar decisiones y evidencias, ver [Análisis y trazabilidad](docs/adr/ANALISIS_Y_TRAZABILIDAD.md).
