from __future__ import annotations
from datetime import datetime, timezone
from app.core.config import settings
from app.services.capabilities import runtime_capabilities
from app.storage.database import check_database

def build_health_payload() -> dict:
    database_ok, database_error = check_database()
    capabilities = runtime_capabilities()
    healthy = database_ok
    return {"status": "ok" if healthy else "degraded", "service": settings.app_name, "version": settings.app_version, "timestamp": datetime.now(timezone.utc).isoformat(), "database": {"status": "ok" if database_ok else "error", "error": database_error}, "quantum": {"backend": settings.quantum_backend, "simulator": capabilities["quantum_simulator"], "required_for_phase": False}, "runtime": capabilities}
