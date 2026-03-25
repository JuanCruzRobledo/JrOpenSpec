"""WebSocket Gateway stub — placeholder until Phase 7 (realtime-infra)."""

from fastapi import FastAPI

app = FastAPI(
    title="Integrador - WebSocket Gateway",
    description="Real-time event hub (stub)",
    version="0.1.0",
)


@app.get("/")
async def root() -> dict:
    """Health endpoint for the gateway stub."""
    return {"status": "gateway stub"}
