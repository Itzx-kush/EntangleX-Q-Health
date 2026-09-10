from fastapi import APIRouter
from app.services.health import build_health_payload
router = APIRouter(tags=["system"])
@router.get("/health", summary="Readiness and capability status")
def health() -> dict:
    return build_health_payload()
