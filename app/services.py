"""Servicios de dominio y adaptadores externos simulados."""
import logging
import sqlite3

from .db import connect, ANALYTICS_DB_PATH

logger = logging.getLogger(__name__)

def log_analytics(owner, reservation_id, event_type, kind, destination):
    """Registra el evento después del commit operativo, con entrega de mejor esfuerzo."""
    try:
        with connect(ANALYTICS_DB_PATH) as c:
            c.execute(
                "INSERT INTO reservation_events(owner,reservation_id,event_type,kind,destination) VALUES(?,?,?,?,?)",
                (owner, reservation_id, event_type, kind, destination),
            )
    except sqlite3.Error:
        logger.exception("No se pudo registrar el evento analítico %s de la reserva %s", event_type, reservation_id)

def archive_finished_trips(owner: str, today: str):
    """Archiva viajes activos del usuario con fecha de fin anterior a hoy."""
    with connect() as c:
        cur = c.execute(
            "UPDATE trips SET status='archived' WHERE owner=? AND status='active' AND end_date < ?",
            (owner, today),
        )
        return cur.rowcount

def enrich_reservation(payload: dict) -> dict:
    """Adaptador de proveedor simulado: normaliza datos sin llamar APIs reales."""
    result = dict(payload)
    result["provider"] = result.get("provider") or "DemoTravel"
    result["status"] = result.get("status") or "confirmed"
    return result

def classify_support(message: str) -> str:
    text = message.lower()
    complex_terms = (
        "reembolso", "demanda", "emergencia", "sobreventa",
        "no puedo viajar", "cancelación urgente",
        "reprogram", "cambiar fecha", "cambio de fecha",
        "modificar fecha", "posponer", "adelantar vuelo",
    )
    return "agency" if any(term in text for term in complex_terms) else "bot"
