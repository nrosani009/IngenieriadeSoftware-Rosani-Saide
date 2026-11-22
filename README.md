# Trotamundos

## 1. ¿Qué es Trotamundos?

Trotamundos es un prototipo académico del TPE de Diseño de Sistemas de Software. Permite organizar reservas por viaje, consultar su estado con un asistente por reglas y ver cómo se simula la derivación de consultas complejas. La aplicación usa FastAPI y dos bases SQLite locales, una para los datos operativos y otra para los eventos analíticos.

## 2. Requisitos previos

- **Python 3.11 o superior.** La última verificación se hizo con Python 3.13. [Descarga oficial de Python](https://www.python.org/downloads/).
- Un navegador web. Las dependencias de Python se instalan con `pip` en el paso 4.

## 3. Obtener el proyecto

Usá la **carpeta entregada**. Si la recibiste como ZIP, descomprimilo primero. Abrí una terminal en la carpeta que contiene `README.md`, `requirements.txt` y `app/`.

El prototipo se entrega como carpeta local. La descarga de un ZIP desde GitHub y la clonación con Git quedan pendientes de una publicación. Para esta entrega no hace falta instalar Git.

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

Dejá abierta la terminal mientras usás el prototipo. Para detenerlo, presioná **Ctrl+C**. Al iniciar, la aplicación crea las bases SQLite si faltan. Opcionalmente, podés cambiar sus rutas con `TROTAMUNDOS_DB` y `TROTAMUNDOS_ANALYTICS_DB`.

## 6. Acceder desde el navegador

- **Interfaz web:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Documentación interactiva de la API (Swagger):** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Estado del servidor:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

## 7. Probar el recorrido principal

1. Abrí la interfaz. El campo **Token** viene con el de Alice, `demo-alice-token`. Para usar a Bob, cambialo por `demo-bob-token`. Hacé clic en **Cargar viajes** para ver los datos del usuario elegido.
2. En **Crear viaje**, escribí un nombre y hacé clic en **Crear viaje**. El ID se copia al formulario de reservas.
3. Elegí un tipo y un proveedor y hacé clic en **Agregar reserva**. Anotá el número que aparece como **Reserva #…** en la tarjeta del viaje.
4. En **Soporte**, escribí «¿Cuál es el estado de mi reserva?», ingresá ese ID y hacé clic en **Consultar asistente**.
5. Enviá «Necesito un reembolso urgente» para ver la derivación simulada a la agencia indicada en el formulario.

Para probar una operación protegida directamente desde Swagger, ingresá `Bearer demo-alice-token` o `Bearer demo-bob-token` en el campo `authorization`. En la interfaz web, ingresá solo el token, sin el prefijo `Bearer`.

## 8. Ejecutar las pruebas

Desde la carpeta del proyecto, con el entorno virtual activo:

```bash
python -m pytest -q
```

En la última verificación, pytest informó 15 pruebas aprobadas.

## 9. Limitaciones

- La demo funciona en local. No requiere servicios externos ni infraestructura en la nube.
- Las integraciones con correo, proveedores y agencias son simuladas. Los tokens fijos son exclusivos de la demo.
- El archivado de viajes vencidos ocurre al cargar el listado activo. La API permite incluir los archivados con `GET /trips?include_archived=true`.
- La analítica separa almacenamiento y consultas. Si falla el registro de un evento, la operación principal puede completarse y el evento puede perderse. El rendimiento, la disponibilidad y la escala de producción quedan fuera de la verificación.

Para consultar decisiones y evidencias, ver [Análisis y trazabilidad](docs/ANALISIS_Y_TRAZABILIDAD.md).
