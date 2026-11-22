from contextlib import asynccontextmanager
from datetime import date, datetime, timezone
from typing import Annotated, Literal
import sqlite3

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import AfterValidator, BaseModel, Field

from .db import ANALYTICS_DB_PATH, init_db, connect, rowdict
from .security import current_user
from .services import log_analytics, archive_finished_trips, enrich_reservation, classify_support

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(
    title="Trotamundos — Prototipo académico",
    description=(
        "API del prototipo académico de Trotamundos. Los endpoints están agrupados "
        "por tarea: viajes, reservas, correo, proveedores, soporte, analítica y sistema. "
        "Las integraciones externas son simuladas. Para empezar, usá el token "
        "`demo-alice-token` en el encabezado Authorization como `Bearer demo-alice-token`."
    ),
    version="0.1.0",
    lifespan=lifespan,
    openapi_tags=[
        {"name": "Viajes", "description": "Crear, consultar, modificar y archivar viajes."},
        {"name": "Reservas", "description": "Administrar reservas vinculadas a tus viajes."},
        {"name": "Correo", "description": "Administrar remitentes permitidos y simular la importación de mensajes."},
        {"name": "Proveedores", "description": "Simular actualizaciones de estado recibidas de proveedores externos."},
        {"name": "Soporte", "description": "Consultar el asistente por reglas y simular la derivación a una agencia."},
        {"name": "Analítica", "description": "Consultar resúmenes guardados en la base analítica separada."},
        {"name": "Sistema", "description": "Comprobar el estado del servicio."},
    ],
)

ReservationKind = Literal["flight", "hotel", "car", "train", "bus", "other"]
ReservationStatus = Literal["confirmed", "cancelled"]

def trip_date(value: str) -> str:
    if date.fromisoformat(value).isoformat() != value:
        raise ValueError("Usá una fecha con formato AAAA-MM-DD")
    return value


def reservation_datetime(value: str) -> datetime:
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=timezone.utc)


def reservation_date(value: str) -> str:
    reservation_datetime(value)
    return value


TripDate = Annotated[str, AfterValidator(trip_date)]
ReservationDate = Annotated[str, AfterValidator(reservation_date)]


def validate_period(start, end, parse):
    if start is not None and end is not None:
        try:
            reversed_period = parse(start) > parse(end)
        except ValueError as exc:
            raise HTTPException(422, "El período contiene una fecha inválida") from exc
        if reversed_period:
            raise HTTPException(422, "La fecha de fin debe ser igual o posterior a la de inicio")


def validate_patch_fields(data, required_fields):
    for field in required_fields:
        if field in data and data[field] is None:
            raise HTTPException(422, f"El campo {field} no admite null")


class TripIn(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    start_date: TripDate | None = None
    end_date: TripDate | None = None

class TripPatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    start_date: TripDate | None = None
    end_date: TripDate | None = None
    status: Literal["active", "archived"] | None = None

class ReservationIn(BaseModel):
    trip_id: int
    kind: ReservationKind
    provider: str = Field(min_length=1, max_length=100)
    confirmation_code: str | None = None
    start_at: ReservationDate | None = None
    end_at: ReservationDate | None = None
    destination: str | None = None
    status: ReservationStatus = "confirmed"

class ReservationPatch(BaseModel):
    trip_id: int | None = None
    kind: ReservationKind | None = None
    provider: str | None = Field(default=None, min_length=1, max_length=100)
    confirmation_code: str | None = None
    start_at: ReservationDate | None = None
    end_at: ReservationDate | None = None
    destination: str | None = None
    status: ReservationStatus | None = None

class WhitelistIn(BaseModel):
    sender: str = Field(min_length=3, max_length=254)

class EmailMessageIn(BaseModel):
    message_id: str
    sender: str
    trip_id: int
    kind: ReservationKind
    provider: str
    confirmation_code: str | None = None
    start_at: ReservationDate | None = None
    end_at: ReservationDate | None = None
    destination: str | None = None

class ProviderUpdateIn(BaseModel):
    status: ReservationStatus
    destination: str | None = None

class SupportIn(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    preferred_agency: str = Field(default="Agencia Demo", min_length=1, max_length=120)
    reservation_id: int | None = Field(default=None, gt=0, description="Reserva propia cuyo estado se consulta.")


class ReservationOut(BaseModel):
    id: int
    trip_id: int
    owner: str
    kind: ReservationKind
    provider: str
    confirmation_code: str | None
    start_at: str | None
    end_at: str | None
    destination: str | None
    status: ReservationStatus
    source: Literal["manual", "email", "provider"]
    updated_at: str


class EmailImported(BaseModel):
    result: Literal["imported"]
    created: Literal[True]
    reservation: ReservationOut


class EmailNotImported(BaseModel):
    result: Literal["duplicate", "rejected_sender"]
    created: Literal[False]


class EventsByKind(BaseModel):
    kind: ReservationKind
    events: int


class EventsByDestination(BaseModel):
    destination: str
    events: int


class EventsByDate(BaseModel):
    date: date
    events: int


class AnalyticsSummary(BaseModel):
    storage: Literal["separate-analytics-database"]
    events_by_kind: list[EventsByKind]
    events_by_destination: list[EventsByDestination]
    events_by_date: list[EventsByDate]
    updated_events: int
    cancellations: int


def owned_trip(conn, trip_id: int, owner: str):
    row = conn.execute("SELECT * FROM trips WHERE id=? AND owner=?", (trip_id, owner)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")
    return row

def owned_reservation(conn, reservation_id: int, owner: str):
    row = conn.execute("SELECT * FROM reservations WHERE id=? AND owner=?", (reservation_id, owner)).fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Reserva no encontrada")
    return row

@app.get("/", response_class=HTMLResponse)
def home():
    return """<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Trotamundos</title>
<style>
:root{
  --bg:#f3f6fb; --panel:#ffffff; --line:#dfe7f3; --text:#1f2a37; --muted:#667085; --primary:#1d4ed8; --primary-soft:#e8f0ff; --success:#15803d; --warning:#b45309; --shadow:0 12px 32px rgba(15,23,42,0.08);
}
*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,sans-serif;background:linear-gradient(180deg,#eef4ff 0%,var(--bg) 220px);color:var(--text)}
.container{max-width:1180px;margin:0 auto;padding:32px 20px 48px}
header{display:flex;justify-content:space-between;align-items:center;gap:20px;margin-bottom:22px}
.brand h1{margin:0;font-size:2rem} .brand p{margin:6px 0 0;color:var(--muted)}
.badge{display:inline-flex;align-items:center;padding:8px 12px;border-radius:999px;background:var(--primary-soft);color:var(--primary);font-weight:700;font-size:.82rem}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:18px}
.card{grid-column:span 12;background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px;box-shadow:var(--shadow)}
@media (min-width: 900px){.card.wide{grid-column:span 8}.card.medium{grid-column:span 4}.card.small{grid-column:span 6}}
label{display:block;font-size:.9rem;font-weight:600;margin-bottom:8px;color:var(--text)}
input,select,button,textarea{font:inherit}
input,select,textarea{width:100%;padding:11px 12px;border:1px solid var(--line);border-radius:10px;background:#fff;color:var(--text)}
input:focus,select:focus,textarea:focus{outline:2px solid rgba(29,78,216,.12);border-color:#9db7ff}
button{cursor:pointer;border:none;border-radius:10px;padding:11px 14px;background:var(--primary);color:white;font-weight:700;transition:.2s ease}button:hover{filter:brightness(1.04)}button.secondary{background:#eef2ff;color:var(--primary)}button.ghost{background:#f7f9fc;color:var(--text);border:1px solid var(--line)}
.row{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.row.three{grid-template-columns:repeat(3,minmax(0,1fr))}
.field{margin-bottom:12px}
.meta{margin-top:8px;color:var(--muted);font-size:.84rem}
pre{margin:0;background:#f7f9fc;border:1px solid var(--line);border-radius:12px;padding:14px;white-space:pre-wrap;word-break:break-word;max-height:480px;overflow:auto;color:#1f2937}
.kpis{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin-top:10px}
.kpi{padding:14px;border-radius:12px;background:#f8fafc;border:1px solid var(--line)}
.kpi strong{display:block;font-size:1.2rem;margin-top:8px}.kpi span{color:var(--muted);font-size:.8rem}
a.link{color:var(--primary);text-decoration:none;font-weight:600}
.trip-list{display:grid;gap:14px}
.trip-card{border:1px solid var(--line);border-radius:12px;padding:16px;background:#fff}
.trip-head{display:flex;justify-content:space-between;align-items:flex-start;gap:14px}
.trip-head h3{margin:0 0 6px}
.trip-meta,.reservation-meta{color:var(--muted);font-size:.88rem}
.status{border-radius:999px;padding:5px 9px;background:#ecfdf3;color:var(--success);font-size:.78rem;font-weight:700;white-space:nowrap}
.status.archived{background:#fff7ed;color:var(--warning)}
.reservation-list{display:grid;gap:8px;margin-top:12px}
.reservation{padding:11px 12px;border-radius:10px;background:#f7f9fc}
.reservation strong{display:block;margin-bottom:3px}
.empty-state,.notice{padding:14px;border-radius:10px;background:#f7f9fc;color:var(--muted)}
.notice{margin-top:12px}
.guide-list{padding-left:22px;line-height:1.7}
@media (max-width:640px){.container{padding:20px 14px 36px}header{align-items:flex-start;flex-direction:column}.row,.row.three{grid-template-columns:1fr}.kpis{grid-template-columns:1fr}.trip-head{flex-direction:column}}
</style></head><body>
<div class="container">
  <header>
    <div class="brand">
      <div class="badge">Prototipo académico</div>
      <h1>Trotamundos</h1>
      <p>Gestión de viajes y soporte para la demostración del TPE.</p>
    </div>
    <div>
      <a class="link" href="#guia">Guía de uso</a>
      &nbsp;·&nbsp;
      <a class="link" href="/docs" target="_blank" rel="noopener">API para pruebas técnicas</a>
    </div>
  </header>

  <div class="grid">
    <section class="card wide">
      <h2>Acceso de demostración</h2>
      <div class="row">
        <div class="field">
          <label for="token">Token</label>
          <input id="token" value="demo-alice-token" placeholder="demo-alice-token">
        </div>
        <div class="field" style="align-self:end">
          <label>&nbsp;</label>
          <button onclick="loadTrips()">Cargar viajes</button>
        </div>
      </div>
      <div class="meta">Tokens disponibles: demo-alice-token / demo-bob-token</div>
    </section>

    <section class="card medium">
      <h2>Sobre esta demo</h2>
      <p>Permite probar la gestión de viajes, reservas y consultas de soporte. El correo y los proveedores externos son simulados.</p>
      <a class="link" href="#guia">¿Cómo empiezo?</a>
    </section>

    <section class="card small">
      <h2>Crear viaje</h2>
      <div class="field">      <label for="tripName">Nombre</label><input id="tripName" placeholder="Ej: Viaje a Madrid"></div>
      <div class="row">
        <div class="field"><label for="tripStart">Inicio</label><input id="tripStart" type="date"></div>
        <div class="field"><label for="tripEnd">Fin</label><input id="tripEnd" type="date"></div>
      </div>
      <button class="secondary" onclick="createTrip()">Crear viaje</button>
    </section>

    <section class="card small">
      <h2>Crear reserva</h2>
      <div class="field"><label for="tripId">ID del viaje</label><input id="tripId" type="number" placeholder="Ej: 1"></div>
      <div class="row">
        <div class="field"><label for="kind">Tipo</label><select id="kind"><option value="flight">Vuelo</option><option value="hotel">Hotel</option><option value="car">Auto</option><option value="train">Tren</option><option value="bus">Autobús</option></select></div>
        <div class="field"><label for="provider">Proveedor</label><input id="provider" value="DemoTravel"></div>
      </div>
      <div class="row">
        <div class="field"><label for="destination">Destino</label><input id="destination" placeholder="Madrid"></div>
        <div class="field"><label for="confirmation">Código</label><input id="confirmation" placeholder="ABC123"></div>
      </div>
      <button onclick="createReservation()">Agregar reserva</button>
    </section>

    <section class="card wide">
      <h2>Mis viajes y reservas</h2>
      <div style="display:flex; justify-content:space-between; align-items:center; gap:12px; margin-bottom:12px">
        <div class="meta">Listado con reservas agrupadas por viaje.</div>
        <button class="ghost" onclick="loadTrips()">Actualizar</button>
      </div>
      <div id="output" class="trip-list"><div class="empty-state">Ingresá tu token y presioná “Cargar viajes” para ver tus viajes.</div></div>
    </section>

    <section class="card wide">
      <h2>Soporte</h2>
      <div class="field"><label for="support">Consulta</label><textarea id="support" rows="4" placeholder="Describí el problema, por ejemplo: Necesito un reembolso urgente."></textarea></div>
      <div class="field"><label for="supportReservationId">ID de reserva para consultar su estado (opcional)</label><input id="supportReservationId" type="number" min="1" step="1"></div>
      <div class="field"><label for="preferredAgency">Agencia preferida</label><input id="preferredAgency" value="Agencia Demo"></div>
      <button class="secondary" onclick="support()">Consultar asistente</button>
      <div class="meta" style="margin-top:12px">Se clasifica por reglas simples y deriva casos complejos a la agencia preferida.</div>
      <div id="supportOutput" class="notice">Escribí una consulta para recibir una respuesta.</div>
    </section>

    <section class="card" id="guia">
      <h2>Guía rápida</h2>
      <ol class="guide-list">
        <li>Dejá el token de Alice o elegí el de Bob y presioná <strong>Cargar viajes</strong>.</li>
        <li>Creá un viaje. Su ID se completará automáticamente en el formulario de reservas.</li>
        <li>Agregá una reserva y consultá el resultado en <strong>Mis viajes y reservas</strong>.</li>
        <li>Probá el asistente de soporte. Los casos complejos se derivan de forma simulada.</li>
      </ol>
      <p><strong>¿Para qué sirve “API para pruebas técnicas”?</strong> Abre Swagger, una herramienta para explorar y probar endpoints directamente. No hace falta usarla para el recorrido normal de esta página.</p>
      <p class="meta">Las respuestas de la API están en JSON, pero esta página las presenta en tarjetas para que no tengas que leer ese formato técnico.</p>
    </section>
  </div>
</div>
<script>
function auth(){return {'Authorization':'Bearer '+document.getElementById('token').value,'Content-Type':'application/json'}}
async function req(url,opts={}){const r=await fetch(url,{...opts,headers:{...auth(),...(opts.headers||{})}});const d=await r.json();if(!r.ok)throw Error(JSON.stringify(d));return d}
function addText(parent,tag,text,className){const element=document.createElement(tag);element.textContent=text;if(className)element.className=className;parent.appendChild(element);return element}
function renderTrips(trips){
  const output=document.getElementById('output');
  output.replaceChildren();
  if(!trips.length){addText(output,'div','Todavía no hay viajes para mostrar. Podés crear uno en el formulario.','empty-state');return}
  for(const trip of trips){
    const card=document.createElement('article');card.className='trip-card';
    const head=document.createElement('div');head.className='trip-head';
    const title=document.createElement('div');
    addText(title,'h3',trip.name);
    const dates=[trip.start_date?`Inicio ${trip.start_date}`:null,trip.end_date?`Fin ${trip.end_date}`:null].filter(Boolean);
    addText(title,'div',`Viaje #${trip.id}${dates.length?' · '+dates.join(' · '):''}`,'trip-meta');
    head.appendChild(title);
    addText(head,'span',trip.status==='archived'?'Archivado':'Activo',`status${trip.status==='archived'?' archived':''}`);
    card.appendChild(head);
    const reservations=trip.reservations||[];
    if(!reservations.length){addText(card,'div','Este viaje todavía no tiene reservas.','empty-state')}
    else{
      const list=document.createElement('div');list.className='reservation-list';
      for(const reservation of reservations){
        const item=document.createElement('div');item.className='reservation';
        const kindNames={flight:'Vuelo',hotel:'Hotel',car:'Auto',train:'Tren',bus:'Autobús',other:'Otro'};
        addText(item,'strong',`${kindNames[reservation.kind]||reservation.kind} · ${reservation.destination||'Destino pendiente'}`);
        const details=[`Reserva #${reservation.id}`,reservation.provider,reservation.confirmation_code?`Código: ${reservation.confirmation_code}`:null,reservation.status==='cancelled'?'Cancelada':'Confirmada'].filter(Boolean).join(' · ');
        addText(item,'div',details,'reservation-meta');
        list.appendChild(item);
      }
      card.appendChild(list);
    }
    output.appendChild(card);
  }
}
async function loadTrips(){try{renderTrips(await req('/trips'))}catch(e){document.getElementById('output').replaceChildren();addText(document.getElementById('output'),'div','No se pudieron cargar los viajes. Revisá el token e intentá nuevamente.','empty-state')}}
async function createTrip(){
  const name=document.getElementById('tripName').value.trim();
  if(!name){alert('Ingresá un nombre para el viaje.');return}
  try{
    const trip=await req('/trips',{method:'POST',body:JSON.stringify({name,start_date:document.getElementById('tripStart').value||null,end_date:document.getElementById('tripEnd').value||null})});
    document.getElementById('tripId').value=trip.id;
    document.getElementById('tripName').value='';
    await loadTrips();
    alert(`Viaje creado. Su ID (${trip.id}) ya está listo para agregar una reserva.`);
  }catch(e){alert('No se pudo crear el viaje. Revisá el token y los datos.')}
}
async function createReservation(){
  const tripId=Number(document.getElementById('tripId').value);
  if(!Number.isInteger(tripId)||tripId<1){alert('Creá un viaje o ingresá un ID válido.');return}
  try{
    await req('/reservations',{method:'POST',body:JSON.stringify({trip_id:tripId,kind:document.getElementById('kind').value,provider:document.getElementById('provider').value,destination:document.getElementById('destination').value||null,confirmation_code:document.getElementById('confirmation').value||null})});
    await loadTrips();
    alert('Reserva agregada al viaje.');
  }catch(e){alert('No se pudo agregar la reserva. Verificá el ID del viaje y los datos.')}
}
async function support(){
  const output=document.getElementById('supportOutput');
  const message=document.getElementById('support').value.trim();
  if(!message){output.textContent='Escribí una consulta antes de enviar.';return}
  try{
    const reservationId=document.getElementById('supportReservationId').value;
    const result=await req('/support',{method:'POST',body:JSON.stringify({message,preferred_agency:document.getElementById('preferredAgency').value,reservation_id:reservationId?Number(reservationId):null})});
    output.textContent=result.response;
  }catch(e){output.textContent='No se pudo enviar la consulta. Revisá el token e intentá nuevamente.'}
}
</script></body></html>"""

@app.get(
    "/health",
    tags=["Sistema"],
    summary="Comprobar estado del servicio",
    description="Endpoint público para verificar que la API responde.",
)
def health():
    return {"status": "ok", "prototype": True}

@app.post(
    "/trips",
    status_code=201,
    tags=["Viajes"],
    summary="Crear un viaje",
    description="Crea un viaje para el usuario autenticado. Las fechas son opcionales.",
)
def create_trip(payload: TripIn, owner: str = Depends(current_user)):
    validate_period(payload.start_date, payload.end_date, date.fromisoformat)
    with connect() as c:
        cur = c.execute("INSERT INTO trips(owner,name,start_date,end_date) VALUES(?,?,?,?)",
                        (owner, payload.name, payload.start_date, payload.end_date))
        return rowdict(c.execute("SELECT * FROM trips WHERE id=?", (cur.lastrowid,)).fetchone())

@app.get(
    "/trips/{trip_id}",
    tags=["Viajes"],
    summary="Ver un viaje y sus reservas",
    description="Devuelve el viaje del usuario y las reservas asociadas. No permite consultar viajes de otras cuentas.",
)
def get_trip(trip_id: int, owner: str = Depends(current_user)):
    with connect() as c:
        trip = rowdict(owned_trip(c, trip_id, owner))
        trip["reservations"] = [
            rowdict(r) for r in c.execute(
                "SELECT * FROM reservations WHERE trip_id=? AND owner=? ORDER BY start_at, id",
                (trip_id, owner),
            ).fetchall()
        ]
        return trip

@app.get(
    "/trips",
    tags=["Viajes"],
    summary="Listar mis viajes",
    description="Devuelve tus viajes con sus reservas agrupadas. Al pedir el listado activo, archiva tus viajes vencidos.",
)
def list_trips(include_archived: bool = False, owner: str = Depends(current_user)):
    if not include_archived:
        archive_finished_trips(owner, date.today().isoformat())
    with connect() as c:
        query = "SELECT * FROM trips WHERE owner=?"
        args = [owner]
        if not include_archived:
            query += " AND status='active'"
        query += " ORDER BY start_date, id"
        trips = [rowdict(r) for r in c.execute(query, args).fetchall()]
        for trip in trips:
            trip["reservations"] = [rowdict(r) for r in c.execute(
                "SELECT * FROM reservations WHERE trip_id=? AND owner=? ORDER BY start_at,id",
                (trip["id"], owner)).fetchall()]
        return trips

@app.patch(
    "/trips/{trip_id}",
    tags=["Viajes"],
    summary="Modificar un viaje",
    description="Actualiza solo los campos enviados del viaje propio.",
)
def update_trip(trip_id: int, payload: TripPatch, owner: str = Depends(current_user)):
    data = payload.model_dump(exclude_unset=True)
    validate_patch_fields(data, ("name", "status"))
    with connect() as c:
        old = owned_trip(c, trip_id, owner)
        if not data:
            return rowdict(old)
        if "start_date" in data or "end_date" in data:
            validate_period(data.get("start_date", old["start_date"]), data.get("end_date", old["end_date"]), date.fromisoformat)
        assignments = []
        values = []
        for key, value in data.items():
            assignments.append(f"{key}=?")
            values.append(value)
        values.extend([trip_id, owner])
        c.execute(f"UPDATE trips SET {','.join(assignments)} WHERE id=? AND owner=?", values)
        return rowdict(c.execute("SELECT * FROM trips WHERE id=?", (trip_id,)).fetchone())

@app.delete(
    "/trips/{trip_id}",
    status_code=204,
    tags=["Viajes"],
    summary="Eliminar un viaje",
    description="Elimina un viaje propio y sus reservas asociadas.",
)
def delete_trip(trip_id: int, owner: str = Depends(current_user)):
    with connect() as c:
        owned_trip(c, trip_id, owner)
        c.execute("DELETE FROM trips WHERE id=? AND owner=?", (trip_id, owner))
    return None

@app.post(
    "/reservations",
    status_code=201,
    response_model=ReservationOut,
    tags=["Reservas"],
    summary="Agregar una reserva",
    description="Crea una reserva manual dentro de uno de tus viajes.",
)
def create_reservation(payload: ReservationIn, owner: str = Depends(current_user)):
    validate_period(payload.start_at, payload.end_at, reservation_datetime)
    with connect() as c:
        owned_trip(c, payload.trip_id, owner)
        data = enrich_reservation(payload.model_dump())
        cur = c.execute("""INSERT INTO reservations(trip_id,owner,kind,provider,confirmation_code,start_at,end_at,destination,status,source)
            VALUES(?,?,?,?,?,?,?,?,?,'manual')""",
            (data["trip_id"], owner, data["kind"], data["provider"], data["confirmation_code"],
             data["start_at"], data["end_at"], data["destination"], data["status"]))
        rid = cur.lastrowid
        reservation = rowdict(c.execute("SELECT * FROM reservations WHERE id=?", (rid,)).fetchone())
    log_analytics(owner, rid, "created", reservation["kind"], reservation["destination"])
    return reservation

@app.patch(
    "/reservations/{reservation_id}",
    tags=["Reservas"],
    response_model=ReservationOut,
    summary="Modificar una reserva",
    description="Actualiza los campos enviados de una reserva propia.",
)
def update_reservation(reservation_id: int, payload: ReservationPatch, owner: str = Depends(current_user)):
    data = payload.model_dump(exclude_unset=True)
    validate_patch_fields(data, ("trip_id", "kind", "provider", "status"))
    with connect() as c:
        old = owned_reservation(c, reservation_id, owner)
        if "start_at" in data or "end_at" in data:
            validate_period(data.get("start_at", old["start_at"]), data.get("end_at", old["end_at"]), reservation_datetime)
        if "trip_id" in data:
            owned_trip(c, data["trip_id"], owner)
        if not data:
            return rowdict(old)
        data["updated_at"] = "CURRENT_TIMESTAMP"
        assignments = []
        values = []
        for key, value in data.items():
            if key == "updated_at":
                assignments.append("updated_at=CURRENT_TIMESTAMP")
            else:
                assignments.append(f"{key}=?")
                values.append(value)
        values.append(reservation_id)
        values.append(owner)
        c.execute(f"UPDATE reservations SET {','.join(assignments)} WHERE id=? AND owner=?", values)
        updated = rowdict(c.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone())
    event_type = "manual_cancelled" if old["status"] != "cancelled" and updated["status"] == "cancelled" else "updated"
    log_analytics(owner, reservation_id, event_type, updated["kind"], updated["destination"])
    return updated

@app.delete(
    "/reservations/{reservation_id}",
    status_code=204,
    tags=["Reservas"],
    summary="Eliminar una reserva",
    description="Elimina una reserva propia.",
)
def delete_reservation(reservation_id: int, owner: str = Depends(current_user)):
    with connect() as c:
        old = owned_reservation(c, reservation_id, owner)
        c.execute("DELETE FROM reservations WHERE id=? AND owner=?", (reservation_id, owner))
    log_analytics(owner, reservation_id, "deleted", old["kind"], old["destination"])
    return None

@app.post(
    "/whitelist",
    status_code=201,
    tags=["Correo"],
    summary="Permitir un remitente",
    description="Agrega un remitente a tu lista de confianza para la ingesta simulada.",
)
def add_whitelist(payload: WhitelistIn, owner: str = Depends(current_user)):
    sender = payload.sender.strip().lower()
    try:
        with connect() as c:
            cur = c.execute("INSERT INTO whitelist(owner,sender) VALUES(?,?)", (owner, sender))
            return rowdict(c.execute("SELECT * FROM whitelist WHERE id=?", (cur.lastrowid,)).fetchone())
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="El remitente ya está en la whitelist")

@app.get(
    "/whitelist",
    tags=["Correo"],
    summary="Ver mis remitentes permitidos",
    description="Lista los remitentes de confianza configurados para tu cuenta.",
)
def list_whitelist(owner: str = Depends(current_user)):
    with connect() as c:
        return [rowdict(r) for r in c.execute("SELECT * FROM whitelist WHERE owner=? ORDER BY sender", (owner,)).fetchall()]

@app.delete(
    "/whitelist/{entry_id}",
    status_code=204,
    tags=["Correo"],
    summary="Quitar un remitente permitido",
    description="Elimina una entrada propia de la lista de confianza.",
)
def delete_whitelist(entry_id: int, owner: str = Depends(current_user)):
    with connect() as c:
        cur = c.execute("DELETE FROM whitelist WHERE id=? AND owner=?", (entry_id, owner))
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Entrada no encontrada")
    return None

@app.post(
    "/email/ingest",
    response_model=EmailImported | EmailNotImported,
    tags=["Correo"],
    summary="Simular importación de un correo",
    description="Simula el procesamiento de un mensaje ya detectado por un conector externo. Rechaza remitentes no permitidos y evita duplicados por message_id.",
)
def ingest_email(payload: EmailMessageIn, owner: str = Depends(current_user)):
    sender = payload.sender.strip().lower()
    with connect() as c:
        if c.execute("SELECT 1 FROM processed_messages WHERE owner=? AND message_id=?", (owner, payload.message_id)).fetchone():
            return {"result": "duplicate", "created": False}
        if not c.execute("SELECT 1 FROM whitelist WHERE owner=? AND sender=?", (owner, sender)).fetchone():
            c.execute("INSERT INTO processed_messages(owner,message_id,sender,result) VALUES(?,?,?,'rejected_sender')",
                      (owner, payload.message_id, sender))
            return {"result": "rejected_sender", "created": False}
        owned_trip(c, payload.trip_id, owner)
        validate_period(payload.start_at, payload.end_at, reservation_datetime)
        data = enrich_reservation(payload.model_dump())
        cur = c.execute("""INSERT INTO reservations(trip_id,owner,kind,provider,confirmation_code,start_at,end_at,destination,status,source)
            VALUES(?,?,?,?,?,?,?,?,?,'email')""",
            (data["trip_id"], owner, data["kind"], data["provider"], data["confirmation_code"],
             data["start_at"], data["end_at"], data["destination"], data.get("status", "confirmed")))
        rid = cur.lastrowid
        c.execute("INSERT INTO processed_messages(owner,message_id,sender,result,reservation_id) VALUES(?,?,?,'imported',?)",
                  (owner, payload.message_id, sender, rid))
        reservation = rowdict(c.execute("SELECT * FROM reservations WHERE id=?", (rid,)).fetchone())
    log_analytics(owner, rid, "imported_email", reservation["kind"], reservation["destination"])
    return {"result": "imported", "created": True, "reservation": reservation}

@app.post(
    "/provider/reservations/{reservation_id}/update",
    tags=["Proveedores"],
    summary="Simular una actualización del proveedor",
    description="Actualiza el estado de una reserva propia. No realiza una llamada real al proveedor.",
)
def provider_update(reservation_id: int, payload: ProviderUpdateIn, owner: str = Depends(current_user)):
    with connect() as c:
        old = owned_reservation(c, reservation_id, owner)
        c.execute("UPDATE reservations SET status=?, destination=COALESCE(?,destination), source='provider', updated_at=CURRENT_TIMESTAMP WHERE id=? AND owner=?",
                  (payload.status, payload.destination, reservation_id, owner))
        updated = rowdict(c.execute("SELECT * FROM reservations WHERE id=?", (reservation_id,)).fetchone())
    event_type = "provider_cancelled" if old["status"] != "cancelled" and updated["status"] == "cancelled" else "provider_update"
    log_analytics(owner, reservation_id, event_type, updated["kind"], updated["destination"])
    return {"reservation": updated, "adapter": "simulated-provider", "note": "No se invocó una API externa real."}

@app.post(
    "/trips/archive-finished",
    tags=["Viajes"],
    summary="Archivar viajes finalizados",
    description="Archiva tus viajes activos con fecha de fin anterior a hoy. También se ejecuta al consultar el listado activo.",
)
def archive_finished(owner: str = Depends(current_user)):
    count = archive_finished_trips(owner, date.today().isoformat())
    return {"archived_count": count, "policy": "end_date anterior a hoy"}

@app.get(
    "/analytics/summary",
    response_model=AnalyticsSummary,
    tags=["Analítica"],
    summary="Consultar resumen analítico",
    description="Agrupa eventos por tipo, destino y fecha UTC, y cuenta transiciones a cancelada tanto manuales como del proveedor simulado.",
)
def analytics_summary(owner: str = Depends(current_user)):
    with connect(ANALYTICS_DB_PATH) as c:
        by_kind = [dict(r) for r in c.execute(
            "SELECT kind, COUNT(*) AS events FROM reservation_events WHERE owner=? GROUP BY kind ORDER BY events DESC",
            (owner,)).fetchall()]
        by_destination = [dict(r) for r in c.execute(
            "SELECT COALESCE(destination,'(sin destino)') AS destination, COUNT(*) AS events FROM reservation_events WHERE owner=? GROUP BY destination ORDER BY events DESC",
            (owner,)).fetchall()]
        by_date = [dict(r) for r in c.execute(
            "SELECT DATE(event_at) AS date, COUNT(*) AS events FROM reservation_events WHERE owner=? GROUP BY date ORDER BY date",
            (owner,)).fetchall()]
        totals = {r["event_type"]: r["total"] for r in c.execute(
            "SELECT event_type, COUNT(*) AS total FROM reservation_events WHERE owner=? GROUP BY event_type",
            (owner,))}
    return {"storage": "separate-analytics-database", "events_by_kind": by_kind,
            "events_by_destination": by_destination, "events_by_date": by_date,
            "updated_events": totals.get("updated", 0) + totals.get("manual_cancelled", 0),
            "cancellations": totals.get("provider_cancelled", 0) + totals.get("manual_cancelled", 0)}

@app.post(
    "/support",
    tags=["Soporte"],
    summary="Consultar el asistente de soporte",
    description="Consulta el estado de una reserva propia por ID y simula la derivación de casos complejos a la agencia preferida.",
)
def support(payload: SupportIn, owner: str = Depends(current_user)):
    classification = classify_support(payload.message)
    status = "delegated" if classification == "agency" else "answered_by_bot"
    agency = payload.preferred_agency if classification == "agency" else None
    reservation_status = None
    with connect() as c:
        if classification == "bot" and payload.reservation_id is not None and "estado" in payload.message.lower():
            reservation_status = owned_reservation(c, payload.reservation_id, owner)["status"]
        cur = c.execute("INSERT INTO support_cases(owner,message,classification,status,agency) VALUES(?,?,?,?,?)",
                        (owner, payload.message, classification, status, agency))
        case = rowdict(c.execute("SELECT * FROM support_cases WHERE id=?", (cur.lastrowid,)).fetchone())
    if classification == "agency":
        return {"case": case, "response": f"El caso se derivó a {agency}. En este prototipo la derivación es simulada."}
    if reservation_status is not None:
        label = {"confirmed": "confirmada", "cancelled": "cancelada"}[reservation_status]
        return {"case": case, "response": f"La reserva #{payload.reservation_id} está {label}."}
    return {"case": case, "response": "Para consultar el estado de una reserva, indicá su ID y escribí una consulta que incluya la palabra estado."}
