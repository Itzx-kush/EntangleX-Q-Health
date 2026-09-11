from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.explainability.errors import ExplainabilityError
from app.explainability.schemas import ClassicalExplainabilityRequest, ExplainabilityReportListResponse, QuantumExplainabilityRequest
from app.explainability.service import ExplainabilityService


router = APIRouter(prefix="/api/explainability", tags=["explainability"])
_service: ExplainabilityService | None = None


def get_service() -> ExplainabilityService:
    global _service
    if _service is None:
        _service = ExplainabilityService()
    return _service


@router.post("/classical", status_code=201)
def classical(payload: ClassicalExplainabilityRequest, service: ExplainabilityService = Depends(get_service)):
    return service.create_classical(payload)


@router.post("/quantum", status_code=201)
def quantum(payload: QuantumExplainabilityRequest, service: ExplainabilityService = Depends(get_service)):
    return service.create_quantum(payload)


@router.get("/reports", response_model=ExplainabilityReportListResponse)
def list_reports(phase: str | None = Query(default=None), service: ExplainabilityService = Depends(get_service)):
    items = service.list(phase)
    return {"items": items, "total": len(items)}


@router.get("/reports/{report_id}")
def get_report(report_id: str, service: ExplainabilityService = Depends(get_service)):
    return service.get(report_id)
