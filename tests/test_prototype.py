import os
import tempfile
from pathlib import Path
from datetime import date, timedelta

TMP = tempfile.TemporaryDirectory()
os.environ["TROTAMUNDOS_DB"] = str(Path(TMP.name) / "operational.db")
os.environ["TROTAMUNDOS_ANALYTICS_DB"] = str(Path(TMP.name) / "analytics.db")

from fastapi.testclient import TestClient
from app.db import init_db
init_db()
from app.main import app
client = TestClient(app)
ALICE = {"Authorization": "Bearer demo-alice-token"}
BOB = {"Authorization": "Bearer demo-bob-token"}

def test_health_and_auth():
    assert client.get("/health").json()["status"] == "ok"
    assert client.get("/trips").status_code == 401

def test_home_explains_technical_docs_and_trip_display():
    response = client.get("/")
    assert response.status_code == 200
    assert "API para pruebas técnicas" in response.text
    assert "Guía rápida" in response.text
    assert 'id="output" class="trip-list"' in response.text
    assert 'id="supportOutput" class="notice"' in response.text
    assert '<pre id="output">' not in response.text
    assert "req('/trips')" in response.text
    assert 'id="supportReservationId"' in response.text

def test_openapi_endpoints_are_grouped_and_described_in_spanish():
    schema = client.get("/openapi.json").json()
    operations = schema["paths"]
    assert operations["/trips"]["get"]["tags"] == ["Viajes"]
    assert operations["/reservations"]["post"]["tags"] == ["Reservas"]
    assert operations["/email/ingest"]["post"]["tags"] == ["Correo"]
    assert operations["/analytics/summary"]["get"]["tags"] == ["Analítica"]
    assert operations["/trips"]["get"]["summary"] == "Listar mis viajes"
    assert "simula " in operations["/email/ingest"]["post"]["description"].lower()

def test_crud_and_user_isolation():
    t = client.post("/trips", headers=ALICE, json={"name":"Viaje de prueba","start_date":"2030-01-01","end_date":"2030-01-10"})
    assert t.status_code == 201
    tid = t.json()["id"]
    updated_trip = client.patch(f"/trips/{tid}", headers=ALICE, json={"name":"Viaje actualizado", "status":"active"})
    assert updated_trip.status_code == 200
    assert updated_trip.json()["name"] == "Viaje actualizado"
    assert client.get(f"/trips/{tid}", headers=ALICE).json()["id"] == tid
    r = client.post("/reservations", headers=ALICE, json={"trip_id":tid,"kind":"flight","provider":"DemoAir","destination":"Madrid"})
    assert r.status_code == 201
    rid = r.json()["id"]
    assert len(client.get("/trips", headers=ALICE).json()) == 1
    assert client.get("/trips", headers=BOB).json() == []
    assert client.patch(f"/reservations/{rid}", headers=BOB, json={"destination":"Londres"}).status_code == 404
    assert client.patch(f"/reservations/{rid}", headers=ALICE, json={"destination":"Roma"}).json()["destination"] == "Roma"
    assert client.delete(f"/reservations/{rid}", headers=ALICE).status_code == 204
    assert client.delete(f"/trips/{tid}", headers=ALICE).status_code == 204


def test_automatic_grouping_by_unique_trip_date_range():
    trip = client.post("/trips", headers=ALICE, json={
        "name": "Viaje agrupado", "start_date": "2031-04-01", "end_date": "2031-04-10",
    }).json()
    manual = client.post("/reservations", headers=ALICE, json={
        "kind": "flight", "provider": "DemoAir",
        "start_at": "2031-04-03T08:00:00", "end_at": "2031-04-03T10:00:00",
    })
    assert manual.status_code == 201
    assert manual.json()["trip_id"] == trip["id"]
    assert client.get(f"/trips/{trip['id']}", headers=ALICE).json()["reservations"][0]["id"] == manual.json()["id"]
    assert client.post("/whitelist", headers=ALICE, json={"sender": "auto-group@example.com"}).status_code == 201
    email = client.post("/email/ingest", headers=ALICE, json={
        "message_id": "auto-group-2031", "sender": "auto-group@example.com",
        "kind": "hotel", "provider": "DemoStay", "start_at": "2031-04-05T14:00:00",
        "end_at": "2031-04-08T10:00:00",
    })
    assert email.status_code == 200
    assert email.json()["result"] == "imported"
    assert email.json()["reservation"]["trip_id"] == trip["id"]


def test_automatic_grouping_does_not_guess_on_missing_or_ambiguous_dates():
    trip = client.post("/trips", headers=BOB, json={
        "name": "Primer viaje coincidente", "start_date": "2032-05-01", "end_date": "2032-05-10",
    }).json()
    assert client.post("/reservations", headers=BOB, json={
        "kind": "bus", "provider": "DemoBus",
    }).status_code == 422
    assert client.post("/reservations", headers=BOB, json={
        "kind": "bus", "provider": "DemoBus", "start_at": "2032-06-01T12:00:00",
    }).status_code == 422
    assert client.post("/reservations", headers=ALICE, json={
        "kind": "bus", "provider": "DemoBus", "start_at": "2032-05-03T12:00:00",
    }).status_code == 422
    second = client.post("/trips", headers=BOB, json={
        "name": "Segundo viaje coincidente", "start_date": "2032-05-02", "end_date": "2032-05-09",
    })
    assert second.status_code == 201
    ambiguous = client.post("/reservations", headers=BOB, json={
        "kind": "train", "provider": "DemoRail", "start_at": "2032-05-03T12:00:00",
    })
    assert ambiguous.status_code == 409
    explicit = client.post("/reservations", headers=BOB, json={
        "trip_id": trip["id"], "kind": "train", "provider": "DemoRail",
    })
    assert explicit.status_code == 201
    assert explicit.json()["trip_id"] == trip["id"]


def test_whitelist_ingestion_and_idempotency():
    trip = client.post("/trips", headers=ALICE, json={"name":"Correo test"}).json()
    message = {"message_id":"msg-001","sender":"travel@example.com","trip_id":trip["id"],"kind":"hotel","provider":"DemoStay","destination":"Córdoba"}
    rejected = client.post("/email/ingest", headers=ALICE, json=message)
    assert rejected.json()["result"] == "rejected_sender"
    assert client.post("/email/ingest", headers=ALICE, json=message).json()["result"] == "rejected_sender"
    assert client.post("/whitelist", headers=ALICE, json={"sender":"travel@example.com"}).status_code == 201
    # El mismo message_id rechazado puede importarse cuando el remitente es autorizado.
    imported = client.post("/email/ingest", headers=ALICE, json=message)
    assert imported.json()["result"] == "imported"
    assert imported.json()["reservation"]["source"] == "email"
    assert client.post("/email/ingest", headers=ALICE, json=message).json()["result"] == "duplicate"


def test_previously_recorded_rejected_message_can_be_imported():
    from app.db import connect
    trip = client.post("/trips", headers=BOB, json={"name": "Correo histórico"}).json()
    message = {
        "message_id": "legacy-rejected-001", "sender": "legacy@example.com",
        "trip_id": trip["id"], "kind": "train", "provider": "DemoRail",
    }
    # Compatibilidad con rechazos persistidos por versiones anteriores.
    with connect() as c:
        c.execute(
            "INSERT INTO processed_messages(owner,message_id,sender,result) VALUES(?,?,?,'rejected_sender')",
            ("bob", message["message_id"], message["sender"]),
        )
    assert client.post("/email/ingest", headers=BOB, json=message).json()["result"] == "rejected_sender"
    assert client.post("/whitelist", headers=BOB, json={"sender": message["sender"]}).status_code == 201
    imported = client.post("/email/ingest", headers=BOB, json=message)
    assert imported.status_code == 200
    assert imported.json()["result"] == "imported"
    assert client.post("/email/ingest", headers=BOB, json=message).json()["result"] == "duplicate"
    with connect() as c:
        row = c.execute(
            "SELECT result, reservation_id FROM processed_messages WHERE owner=? AND message_id=?",
            ("bob", message["message_id"]),
        ).fetchone()
        assert row["result"] == "imported"
        assert row["reservation_id"] == imported.json()["reservation"]["id"]


def test_provider_adapter_and_analytics():
    trip = client.post("/trips", headers=ALICE, json={"name":"Proveedor"}).json()
    reservation = client.post("/reservations", headers=ALICE, json={"trip_id":trip["id"],"kind":"bus","provider":"DemoBus","destination":"Tandil"}).json()
    updated = client.post(f"/provider/reservations/{reservation['id']}/update", headers=ALICE, json={"status":"cancelled"})
    assert updated.status_code == 200
    assert updated.json()["reservation"]["status"] == "cancelled"
    analytics = client.get("/analytics/summary", headers=ALICE).json()
    assert analytics["storage"] == "separate-analytics-database"
    assert analytics["events_by_kind"]

def test_support_bot_and_agency_escalation():
    simple = client.post("/support", headers=ALICE, json={"message":"¿Cuál es el estado de mi viaje?"}).json()
    assert simple["case"]["classification"] == "bot"
    complex_case = client.post("/support", headers=ALICE, json={"message":"Necesito un reembolso urgente","preferred_agency":"Agencia Norte"}).json()
    assert complex_case["case"]["classification"] == "agency"
    assert complex_case["case"]["status"] == "delegated"
    assert "Agencia Norte" in complex_case["response"]


def test_support_reprogramming_is_escalated_without_modifying_reservation():
    trip = client.post("/trips", headers=ALICE, json={"name": "Viaje para reprogramar"}).json()
    reservation = client.post("/reservations", headers=ALICE, json={
        "trip_id": trip["id"], "kind": "flight", "provider": "DemoAir",
        "start_at": "2030-06-01T10:00:00",
    }).json()
    for message in ("Necesito reprogramar mi vuelo", "Quiero cambiar fecha de mi reserva"):
        response = client.post("/support", headers=ALICE, json={
            "message": message, "reservation_id": reservation["id"],
            "preferred_agency": "Agencia Demo",
        })
        assert response.status_code == 200
        result = response.json()
        assert result["case"]["classification"] == "agency"
        assert result["case"]["status"] == "delegated"
        assert result["case"]["agency"] == "Agencia Demo"
        assert "simulada" in result["response"]
    stored = client.get(f"/trips/{trip['id']}", headers=ALICE).json()["reservations"][0]
    assert stored["start_at"] == "2030-06-01T10:00:00"


def test_finished_trip_archiving():
    past = (date.today() - timedelta(days=3)).isoformat()
    trip = client.post("/trips", headers=ALICE, json={"name":"Viaje finalizado","end_date":past}).json()
    result = client.post("/trips/archive-finished", headers=ALICE)
    assert result.status_code == 200
    assert result.json()["archived_count"] >= 1
    active_ids = [t["id"] for t in client.get("/trips", headers=ALICE).json()]
    assert trip["id"] not in active_ids
    archived = client.get("/trips?include_archived=true", headers=ALICE).json()
    assert next(t for t in archived if t["id"] == trip["id"])["status"] == "archived"


def test_archiving_is_scoped_to_the_authenticated_user():
    past = (date.today() - timedelta(days=1)).isoformat()
    alice = client.post("/trips", headers=ALICE, json={"name": "Vencido Alice", "end_date": past}).json()
    bob = client.post("/trips", headers=BOB, json={"name": "Vencido Bob", "end_date": past}).json()

    result = client.post("/trips/archive-finished", headers=ALICE)
    assert result.status_code == 200
    assert result.json()["archived_count"] == 1
    assert client.get(f"/trips/{alice['id']}", headers=ALICE).json()["status"] == "archived"
    assert client.get(f"/trips/{bob['id']}", headers=BOB).json()["status"] == "active"


def test_active_listing_archives_overdue_trips_on_demand():
    past = (date.today() - timedelta(days=1)).isoformat()
    trip = client.post("/trips", headers=ALICE, json={"name": "Vencido en listado", "end_date": past}).json()
    due_today = client.post("/trips", headers=ALICE, json={"name": "Termina hoy", "end_date": date.today().isoformat()}).json()

    active = client.get("/trips", headers=ALICE)
    assert active.status_code == 200
    active_ids = {row["id"] for row in active.json()}
    assert trip["id"] not in active_ids
    assert due_today["id"] in active_ids
    all_trips = client.get("/trips?include_archived=true", headers=ALICE).json()
    assert next(row for row in all_trips if row["id"] == trip["id"])["status"] == "archived"


def test_reservation_ingestion_and_analytics_contracts():
    trip = client.post("/trips", headers=ALICE, json={"name": "Contratos"}).json()
    reservation_response = client.post("/reservations", headers=ALICE, json={
        "trip_id": trip["id"], "kind": "flight", "provider": "ContratoAir",
    })
    assert reservation_response.status_code == 201
    reservation = reservation_response.json()
    assert reservation == {
        "id": reservation["id"], "trip_id": trip["id"], "owner": "alice",
        "kind": "flight", "provider": "ContratoAir", "status": "confirmed", "source": "manual",
        "confirmation_code": None, "start_at": None, "end_at": None, "destination": None,
        "updated_at": reservation["updated_at"],
    }
    assert reservation["updated_at"]
    message = {
        "message_id": "contrato-correo", "sender": "contratos@example.com",
        "trip_id": trip["id"], "kind": "hotel", "provider": "ContratoStay",
    }
    assert client.post("/whitelist", headers=ALICE, json={"sender": message["sender"]}).status_code == 201
    imported = client.post("/email/ingest", headers=ALICE, json=message)
    assert imported.status_code == 200
    assert set(imported.json()) == {"result", "created", "reservation"}
    assert imported.json()["reservation"]["source"] == "email"
    assert imported.json()["created"] is True
    assert client.post("/email/ingest", headers=ALICE, json=message).json() == {"result": "duplicate", "created": False}

    summary = client.get("/analytics/summary", headers=ALICE)
    assert summary.status_code == 200
    assert set(summary.json()) == {
        "storage", "events_by_kind", "events_by_destination", "events_by_date", "updated_events", "cancellations",
    }
    assert summary.json()["events_by_date"]
    for row in summary.json()["events_by_date"]:
        assert date.fromisoformat(row["date"])
        assert row["events"] > 0

    paths = client.get("/openapi.json").json()["paths"]
    assert paths["/reservations"]["post"]["responses"]["201"]["content"]["application/json"]["schema"]["$ref"].endswith("/ReservationOut")
    assert len(paths["/email/ingest"]["post"]["responses"]["200"]["content"]["application/json"]["schema"]["anyOf"]) == 2
    assert paths["/analytics/summary"]["get"]["responses"]["200"]["content"]["application/json"]["schema"]["$ref"].endswith("/AnalyticsSummary")


def test_analytics_counts_provider_cancellation_transitions():
    before = client.get("/analytics/summary", headers=BOB).json()
    trip = client.post("/trips", headers=BOB, json={"name": "Cancelaciones"}).json()
    reservation = client.post("/reservations", headers=BOB, json={
        "trip_id": trip["id"], "kind": "bus", "provider": "DemoBus",
    }).json()
    rid = reservation["id"]
    assert client.patch(f"/reservations/{rid}", headers=BOB, json={"destination": "Tandil"}).status_code == 200

    for _ in range(2):
        updated = client.post(f"/provider/reservations/{rid}/update", headers=BOB, json={"status": "cancelled"})
        assert updated.json()["reservation"]["status"] == "cancelled"
    after = client.get("/analytics/summary", headers=BOB).json()
    assert after["cancellations"] == before["cancellations"] + 1
    assert after["updated_events"] == before["updated_events"] + 1



def test_analytics_counts_manual_and_provider_cancellation_transitions():
    before = client.get("/analytics/summary", headers=ALICE).json()
    trip = client.post("/trips", headers=ALICE, json={"name": "Cancelaciones de distintos canales"}).json()
    manual = client.post("/reservations", headers=ALICE, json={
        "trip_id": trip["id"], "kind": "hotel", "provider": "DemoStay",
    }).json()
    provider = client.post("/reservations", headers=ALICE, json={
        "trip_id": trip["id"], "kind": "flight", "provider": "DemoAir",
    }).json()
    path = f"/reservations/{manual['id']}"
    first = client.patch(path, headers=ALICE, json={"status": "cancelled"})
    assert first.status_code == 200
    assert first.json()["status"] == "cancelled"
    assert client.patch(path, headers=ALICE, json={"status": "cancelled"}).status_code == 200
    assert client.post(f"/provider/reservations/{provider['id']}/update", headers=ALICE,
                       json={"status": "cancelled"}).status_code == 200
    after = client.get("/analytics/summary", headers=ALICE).json()
    assert after["cancellations"] == before["cancellations"] + 2
    assert after["updated_events"] == before["updated_events"] + 2
    assert client.get("/analytics/summary", headers=BOB).status_code == 200
    # La vuelta a confirmado habilita una nueva transición real a cancelada.
    assert client.patch(path, headers=ALICE, json={"status": "confirmed"}).status_code == 200
    assert client.patch(path, headers=ALICE, json={"status": "cancelled"}).status_code == 200
    again = client.get("/analytics/summary", headers=ALICE).json()
    assert again["cancellations"] == before["cancellations"] + 3


def test_analytics_failure_preserves_operational_write(monkeypatch, tmp_path, caplog):
    from app import services

    monkeypatch.setattr(services, "ANALYTICS_DB_PATH", str(tmp_path / "missing" / "analytics.db"))
    trip = client.post("/trips", headers=ALICE, json={"name": "Fallo analítico"}).json()
    response = client.post("/reservations", headers=ALICE, json={
        "trip_id": trip["id"], "kind": "train", "provider": "DemoRail",
    })
    assert response.status_code == 201
    loaded = client.get(f"/trips/{trip['id']}", headers=ALICE).json()
    assert loaded["reservations"][0]["id"] == response.json()["id"]
    assert "No se pudo registrar el evento analítico" in caplog.text


def test_dates_and_null_validations():
    for invalid in (
        {"name": "Inválido", "start_date": "2030-02-30"},
        {"name": "Invertido", "start_date": "2030-02-02", "end_date": "2030-02-01"},
    ):
        assert client.post("/trips", headers=ALICE, json=invalid).status_code == 422
    trip = client.post("/trips", headers=ALICE, json={
        "name": "Validación", "start_date": "2030-02-01", "end_date": "2030-02-02",
    }).json()
    for invalid in ({"name": None}, {"status": None}, {"end_date": "2030-01-31"}):
        assert client.patch(f"/trips/{trip['id']}", headers=ALICE, json=invalid).status_code == 422

    data = {"trip_id": trip["id"], "kind": "bus", "provider": "DemoBus"}
    invalid_dates = {"start_at": "2030-02-01T10:00:00-03:00", "end_at": "2030-02-01T12:30:00Z"}
    assert client.post("/reservations", headers=ALICE, json={**data, **invalid_dates}).status_code == 422
    sender = "fechas@example.com"
    assert client.post("/whitelist", headers=ALICE, json={"sender": sender}).status_code == 201
    email = {"message_id": "fechas-invalidas", "sender": sender, **data}
    assert client.post("/email/ingest", headers=ALICE, json={**email, **invalid_dates}).status_code == 422
    assert client.post("/email/ingest", headers=ALICE, json=email).json()["result"] == "imported"

    reservation = client.post("/reservations", headers=ALICE, json={**data, "start_at": "2030-02-01"}).json()
    path = f"/reservations/{reservation['id']}"
    for invalid in (
        {"provider": None}, {"status": None}, {"trip_id": None}, {"kind": None},
        {"end_at": "ayer"}, {"end_at": "2030-01-31"},
    ):
        assert client.patch(path, headers=ALICE, json=invalid).status_code == 422
    assert client.patch(path, headers=ALICE, json={"start_at": None}).json()["start_at"] is None


def test_support_answers_only_for_owned_reservations():
    trip = client.post("/trips", headers=ALICE, json={"name": "Soporte con datos"}).json()
    reservation = client.post("/reservations", headers=ALICE, json={
        "trip_id": trip["id"], "kind": "hotel", "provider": "DemoStay",
    }).json()
    rid = reservation["id"]
    query = {"message": "¿Cuál es el estado de mi reserva?", "reservation_id": rid}
    answer = client.post("/support", headers=ALICE, json=query)
    assert answer.status_code == 200
    assert answer.json()["response"] == f"La reserva #{rid} está confirmada."
    assert answer.json()["case"]["status"] == "answered_by_bot"
    assert client.post("/support", headers=BOB, json=query).status_code == 404
    assert client.post(f"/provider/reservations/{rid}/update", headers=ALICE, json={"status": "cancelled"}).status_code == 200
    assert "cancelada" in client.post("/support", headers=ALICE, json=query).json()["response"]

    escalation = client.post("/support", headers=ALICE, json={
        **query, "message": "Necesito un reembolso", "preferred_agency": "Agencia Sur",
    })
    assert escalation.json()["case"]["agency"] == "Agencia Sur"
    assert escalation.json()["case"]["status"] == "delegated"
    assert "simulada" in escalation.json()["response"]
