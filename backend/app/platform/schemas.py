from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field

class PlatformLimits(BaseModel):
    max_upload_mb: int
    max_qubits: int
    max_shots: int
    max_batch_predictions: int
    max_federated_sites: int
    max_federated_rounds: int
    artifact_retention_days: int
    cache_ttl_seconds: int
    raw_records_in_logs: bool = False

class SecurityScanRequest(BaseModel):
    file_name: str
    content_type: str | None = None
    size_bytes: int = Field(ge=0)
    column_names: list[str] = Field(default_factory=list)
    sample_values: dict[str, Any] | None = None

class SecurityScanResponse(BaseModel):
    accepted: bool
    sanitized_file_name: str
    findings: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raw_values_retained: bool = False
    deidentification_required: bool

class HardwareCompatibilityRequest(BaseModel):
    backend_name: str
    qubits: int = Field(ge=1)
    shots: int = Field(ge=1)
    circuit_depth: int = Field(default=1, ge=1)
    estimated_timeout_seconds: int = Field(default=300, ge=1)

class HardwareStatus(BaseModel):
    simulator_backend: str
    hardware_enabled: bool
    provider_configured: bool
    available_backends: list[str]
    queue_time_status: Literal["not_requested", "unavailable_without_provider", "provider_required"]
    cost_status: Literal["not_requested", "unavailable_without_provider", "provider_required"]
    calibration_status: Literal["not_requested", "unavailable_without_provider", "provider_required"]
    scientific_warnings: list[str] = Field(default_factory=list)

class HardwareCompatibilityResponse(BaseModel):
    compatible: bool
    execution_mode: Literal["simulator", "hardware", "unavailable"]
    backend_name: str
    reasons: list[str] = Field(default_factory=list)
    provenance_requirements: list[str] = Field(default_factory=list)
    evidence_status: Literal["available", "unavailable", "not_run"]

class AuditEvent(BaseModel):
    id: int
    created_at: str
    method: str
    path: str
    status_code: int
    principal: str
    request_id: str
    resource_type: str | None = None
    resource_id: str | None = None

class AuditEventList(BaseModel):
    items: list[AuditEvent]
    total: int

class FederatedSite(BaseModel):
    site_id: str = Field(min_length=1, max_length=80)
    sample_count: int = Field(ge=1)
    feature_count: int = Field(ge=1)
    parameter_vector: list[float] = Field(min_length=1)
    dataset_fingerprint: str | None = None

class FederatedSandboxRequest(BaseModel):
    sites: list[FederatedSite] = Field(min_length=2, max_length=8)
    rounds: int = Field(default=1, ge=1, le=10)
    aggregation: Literal["weighted_mean"] = "weighted_mean"
    seed: int = 42

class FederatedSandboxResponse(BaseModel):
    sandbox_id: str
    rounds: int
    site_count: int
    parameter_count: int
    aggregation: str
    aggregated_parameters: list[float]
    site_metadata: list[dict[str, Any]]
    raw_records_transferred: bool = False
    scientific_warnings: list[str] = Field(default_factory=list)

class ValidationMatrixRow(BaseModel):
    requirement: str
    feature: str
    api: str
    ui_screen: str
    test: str
    evidence_artifact: str
    demo_step: str
    limitation: str

class ValidationMatrix(BaseModel):
    problem_id: str
    rows: list[ValidationMatrixRow]
    status: Literal["draft", "ready_for_demo"]

class PlatformReadiness(BaseModel):
    phase_19_status: Literal["ready", "partial", "blocked"]
    phase_20_status: Literal["ready", "partial", "blocked"]
    controls: dict[str, bool]
    limitations: list[str] = Field(default_factory=list)
