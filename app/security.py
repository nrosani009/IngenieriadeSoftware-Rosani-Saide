"""Autenticación mínima de demostración. No apta para producción."""
from fastapi import Header, HTTPException

DEMO_TOKENS = {
    "demo-alice-token": "alice",
    "demo-bob-token": "bob",
}

def current_user(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Se requiere Bearer token")
    token = authorization.removeprefix("Bearer ").strip()
    user = DEMO_TOKENS.get(token)
    if not user:
        raise HTTPException(status_code=401, detail="Token inválido")
    return user
