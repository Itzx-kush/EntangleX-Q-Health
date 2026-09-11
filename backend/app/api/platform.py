from __future__ import annotations
from fastapi import APIRouter, Depends, Query
from app.platform.schemas import (
    AuditEventList, FederatedSandboxRequest, FederatedSandboxResponse,
    HardwareCompatibilityRequest, HardwareCompatibilityResponse, HardwareStatus,
    PlatformLimits, PlatformReadiness, SecurityScanRequest, SecurityScanResponse,
    ValidationMatrix,
)
from app.platform.service import PlatformGovernanceService

router = APIRouter(prefix="/api/platform", tags=["platform-governance"])
_service: PlatformGovernanceService | None = None

def get_platform_service() -> PlatformGovernanceService:
    global _service
    if _service is None:
        _service = PlatformGovernanceService()
    return _service

@router.get("/limits", response_model=PlatformLimits)
def limits(service: PlatformGovernanceService = Depends(get_platform_service)):
    return service.limits()

@router.get("/security/checklist")
def security_checklist(service: PlatformGovernanceService = Depends(get_platform_service)):
    return {"items": service.security_checklist()}

@router.post("/security/scan", response_model=SecurityScanResponse)
def security_scan(payload: SecurityScanRequest, service: PlatformGovernanceService = Depends(get_platform_service)):
    return service.scan_security(payload)

@router.get("/audit/events", response_model=AuditEventList)
def audit_events(limit: int = Query(default=50, ge=1, le=200), service: PlatformGovernanceService = Depends(get_platform_service)):
    return service.audit_events(limit)

@router.get("/hardware/status", response_model=HardwareStatus)
def hardware_status(service: PlatformGovernanceService = Depends(get_platform_service)):
    return service.hardware_status()

@router.post("/hardware/compatibility", response_model=HardwareCompatibilityResponse)
def hardware_compatibility(payload: HardwareCompatibilityRequest, service: PlatformGovernanceService = Depends(get_platform_service)):
    return service.hardware_compatibility(payload)

@router.post("/federated/sandbox", response_model=FederatedSandboxResponse)
def federated_sandbox(payload: FederatedSandboxRequest, service: PlatformGovernanceService = Depends(get_platform_service)):
    try:
        return service.federated_sandbox(payload)
    except ValueError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@router.get("/validation/matrix", response_model=ValidationMatrix)
def validation_matrix(service: PlatformGovernanceService = Depends(get_platform_service)):
    return service.validation_matrix()

@router.get("/readiness", response_model=PlatformReadiness)
def readiness(service: PlatformGovernanceService = Depends(get_platform_service)):
    return service.readiness()
