from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import json
import os
import re
import sqlite3
import uuid
from pathlib import Path
from typing import Any
from app.core.config import settings
from app.storage.database import sqlite_path
from app.platform.schemas import (
    AuditEventList, FederatedSandboxRequest, FederatedSandboxResponse,
    HardwareCompatibilityRequest, HardwareCompatibilityResponse, HardwareStatus,
    PlatformLimits, PlatformReadiness, SecurityScanRequest, SecurityScanResponse,
    ValidationMatrix,
)

class PlatformGovernanceService:
    """Small, SQLite-backed governance service with privacy-safe payload handling."""
    _phi_patterns = re.compile(r"(patient|medical|mrn|ssn|social|dob|birth|phone|mobile|email|address|name|insurance|member|health|diagnos|treatment|record)", re.I)
    _email_pattern = re.compile(r"\b[^\s@]+@[^\s@]+\.[^\s@]+\b")
    _allowed_extensions = {".csv", ".xlsx", ".json"}

    def __init__(self, database_url: str | None = None):
        self.database_url = database_url or settings.database_url
        self._ensure_tables()

    def _connect(self) -> sqlite3.Connection:
        path = sqlite_path(self.database_url)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(path)
        connection.row_factory = sqlite3.Row
        return connection

    def _ensure_tables(self) -> None:
        with self._connect() as connection:
            connection.executescript("""
                CREATE TABLE IF NOT EXISTS platform_audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status_code INTEGER NOT NULL,
                    principal TEXT NOT NULL,
                    request_id TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT
                );
                CREATE INDEX IF NOT EXISTS idx_platform_audit_created ON platform_audit_events(created_at);
                CREATE INDEX IF NOT EXISTS idx_platform_audit_path ON platform_audit_events(path);
                CREATE TABLE IF NOT EXISTS platform_federated_runs (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    site_count INTEGER NOT NULL,
                    rounds INTEGER NOT NULL,
                    parameter_count INTEGER NOT NULL,
                    metadata_json TEXT NOT NULL
                );
            """)

    def limits(self) -> PlatformLimits:
        return PlatformLimits(
            max_upload_mb=settings.max_upload_size_mb,
            max_qubits=settings.max_qubits,
            max_shots=settings.max_quantum_shots,
            max_batch_predictions=int(os.getenv("MAX_BATCH_PREDICTIONS", "256")),
            max_federated_sites=int(os.getenv("MAX_FEDERATED_SITES", "8")),
            max_federated_rounds=int(os.getenv("MAX_FEDERATED_ROUNDS", "10")),
            artifact_retention_days=int(os.getenv("ARTIFACT_RETENTION_DAYS", "90")),
            cache_ttl_seconds=int(os.getenv("CACHE_TTL_SECONDS", "300")),
        )

    def security_checklist(self) -> list[dict[str, Any]]:
        return [
            {"id": "input_validation", "label": "Validate file name, type and size before parsing", "status": "enabled"},
            {"id": "no_raw_logs", "label": "Never log raw patient or feature values", "status": "enabled"},
            {"id": "env_secrets", "label": "Read provider secrets only from environment variables", "status": "enabled"},
            {"id": "deidentification", "label": "Require de-identification review for PHI/PII-like columns", "status": "review_required"},
            {"id": "audit", "label": "Record request metadata without request bodies", "status": "enabled"},
            {"id": "rbac", "label": "Use authenticated role-aware access at deployment boundary", "status": "deployment_required"},
            {"id": "retention", "label": "Apply configurable artifact retention and cache TTL", "status": "configured"},
        ]

    def scan_security(self, request: SecurityScanRequest) -> SecurityScanResponse:
        original = request.file_name or "unnamed-upload"
        safe_name = Path(original).name
        findings: list[str] = []
        warnings: list[str] = []
        suffix = Path(safe_name).suffix.lower()
        if safe_name != original or ".." in Path(original).parts:
            findings.append("PATH_TRAVERSAL_OR_UNSAFE_FILENAME")
        if suffix not in self._allowed_extensions:
            findings.append("UNSUPPORTED_FILE_EXTENSION")
        if request.size_bytes > self.limits().max_upload_mb * 1024 * 1024:
            findings.append("FILE_EXCEEDS_CONFIGURED_LIMIT")
        if request.content_type and suffix == ".csv" and request.content_type not in {"text/csv", "application/csv", "application/octet-stream"}:
            warnings.append("CONTENT_TYPE_EXTENSION_MISMATCH")
        matched_columns = [column for column in request.column_names if self._phi_patterns.search(column)]
        if matched_columns:
            findings.append("PHI_OR_PII_LIKE_COLUMN_NAMES_DETECTED")
            warnings.append("Review and de-identify flagged columns before training.")
        values = request.sample_values or {}
        value_text = json.dumps(values, default=str)
        if self._email_pattern.search(value_text):
            findings.append("EMAIL_PATTERN_DETECTED_IN_SAMPLE")
        if any(key.lower() in {"ssn", "social_security_number", "mrn"} for key in values):
            findings.append("DIRECT_IDENTIFIER_KEY_DETECTED_IN_SAMPLE")
        return SecurityScanResponse(
            accepted=not any(item.startswith(("PATH_", "UNSUPPORTED_", "FILE_EXCEEDS")) for item in findings),
            sanitized_file_name=safe_name,
            findings=findings,
            warnings=warnings,
            deidentification_required=bool(matched_columns or "EMAIL_PATTERN_DETECTED_IN_SAMPLE" in findings or "DIRECT_IDENTIFIER_KEY_DETECTED_IN_SAMPLE" in findings),
        )

    def audit(self, method: str, path: str, status_code: int, principal: str = "anonymous", request_id: str | None = None, resource_type: str | None = None, resource_id: str | None = None) -> None:
        with self._connect() as connection:
            connection.execute(
                "INSERT INTO platform_audit_events(created_at,method,path,status_code,principal,request_id,resource_type,resource_id) VALUES(?,?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), method[:16], path[:512], int(status_code), principal[:80], (request_id or str(uuid.uuid4()))[:80], resource_type, resource_id),
            )

    def audit_events(self, limit: int = 50) -> AuditEventList:
        safe_limit = max(1, min(int(limit), 200))
        with self._connect() as connection:
            rows = connection.execute("SELECT * FROM platform_audit_events ORDER BY id DESC LIMIT ?", (safe_limit,)).fetchall()
        items = [dict(row) for row in rows]
        return AuditEventList(items=items, total=len(items))

    def hardware_status(self) -> HardwareStatus:
        provider_configured = bool(os.getenv("IBM_QUANTUM_TOKEN") or os.getenv("QISKIT_IBM_TOKEN"))
        enabled = bool(settings.enable_real_quantum)
        warnings = ["No hardware job has been executed; queue, cost and calibration are unavailable."]
        if enabled and not provider_configured:
            warnings.append("Hardware execution is enabled but no provider token is configured through the environment.")
        if not enabled:
            warnings.append("Simulator-first mode is active. Hardware execution remains explicitly disabled.")
        available = [settings.quantum_backend, "aer_simulator", "statevector"]
        return HardwareStatus(
            simulator_backend=settings.quantum_backend,
            hardware_enabled=enabled,
            provider_configured=provider_configured,
            available_backends=sorted(set(available)),
            queue_time_status="provider_required",
            cost_status="provider_required",
            calibration_status="provider_required",
            scientific_warnings=warnings,
        )

    def hardware_compatibility(self, request: HardwareCompatibilityRequest) -> HardwareCompatibilityResponse:
        status = self.hardware_status()
        name = request.backend_name.strip()
        simulator_names = {"aer_simulator", "qasm_simulator", "statevector", "statevector_simulator"}
        is_simulator = name in simulator_names or name == settings.quantum_backend
        reasons: list[str] = []
        if request.qubits > settings.max_qubits:
            reasons.append(f"Qubit request exceeds configured maximum of {settings.max_qubits}.")
        if request.shots > settings.max_quantum_shots:
            reasons.append(f"Shot request exceeds configured maximum of {settings.max_quantum_shots}.")
        if request.circuit_depth > int(os.getenv("MAX_CIRCUIT_DEPTH", "80")):
            reasons.append("Circuit depth exceeds the configured research limit.")
        if not name:
            reasons.append("Backend name is required.")
        hardware_request = not is_simulator
        if hardware_request and not status.hardware_enabled:
            reasons.append("Hardware execution is disabled by configuration.")
        if hardware_request and not status.provider_configured:
            reasons.append("No hardware provider token is configured through the environment.")
        if hardware_request:
            reasons.append("Compatibility does not constitute an executed hardware result.")
        compatible = not reasons or (len(reasons) == 1 and reasons[0].startswith("Compatibility does not"))
        return HardwareCompatibilityResponse(
            compatible=compatible,
            execution_mode="simulator" if is_simulator else ("hardware" if compatible else "unavailable"),
            backend_name=name,
            reasons=reasons,
            provenance_requirements=["backend name", "provider/job identifier", "queue and cost metadata", "calibration/noise metadata", "shots and circuit resource counts"],
            evidence_status="not_run" if compatible else "unavailable",
        )

    def federated_sandbox(self, request: FederatedSandboxRequest) -> FederatedSandboxResponse:
        limits = self.limits()
        if len(request.sites) > limits.max_federated_sites:
            raise ValueError(f"At most {limits.max_federated_sites} sandbox sites are supported.")
        dimensions = {len(site.parameter_vector) for site in request.sites}
        feature_counts = {site.feature_count for site in request.sites}
        if len(dimensions) != 1 or len(feature_counts) != 1:
            raise ValueError("All simulated institutions must exchange compatible parameter dimensions.")
        total_samples = sum(site.sample_count for site in request.sites)
        if total_samples <= 0:
            raise ValueError("Federated sample counts must be positive.")
        parameters = [sum(site.parameter_vector[index] * site.sample_count for site in request.sites) / total_samples for index in range(next(iter(dimensions)))]
        run_id = str(uuid.uuid4())
        metadata = [{"site_id": site.site_id, "sample_count": site.sample_count, "feature_count": site.feature_count, "dataset_fingerprint_present": bool(site.dataset_fingerprint)} for site in request.sites]
        with self._connect() as connection:
            connection.execute("INSERT INTO platform_federated_runs VALUES(?,?,?,?,?,?)", (run_id, datetime.now(timezone.utc).isoformat(), len(request.sites), request.rounds, len(parameters), json.dumps(metadata)))
        return FederatedSandboxResponse(
            sandbox_id=run_id,
            rounds=request.rounds,
            site_count=len(request.sites),
            parameter_count=len(parameters),
            aggregation=request.aggregation,
            aggregated_parameters=parameters,
            site_metadata=metadata,
            scientific_warnings=["This is a reproducible metadata/parameter sandbox, not production hospital federated learning.", "Raw patient records never leave a simulated site in this exchange."],
        )

    def validation_matrix(self) -> ValidationMatrix:
        rows = [
            {"requirement":"Biomedical ingestion and preprocessing","feature":"Validation, profiling and leakage-safe preprocessing","api":"/api/datasets, /api/preprocessing","ui_screen":"ML Pipeline","test":"Phase 2–5 backend tests","evidence_artifact":"Dataset summary and preprocessing artifact","demo_step":"Upload licensed sample","limitation":"Research datasets only; provenance must be verified by the operator."},
            {"requirement":"Hybrid quantum-classical models","feature":"Classical baselines, VQC, QSVM and QNN","api":"/api/models, /api/quantum/qml","ui_screen":"Quantum Lab","test":"Phase 6, 9–11 tests","evidence_artifact":"Model run and circuit artifacts","demo_step":"Train one classical and one simulator model","limitation":"Simulator results are not hardware evidence."},
            {"requirement":"Rigorous comparison","feature":"Repeated validation, confidence intervals and resource accounting","api":"/api/benchmarks","ui_screen":"Evidence","test":"Phase 14 tests","evidence_artifact":"Benchmark report","demo_step":"Compare recorded runs","limitation":"No claim is made when evidence is missing or incomparable."},
            {"requirement":"Explainability","feature":"Classical and quantum sensitivity/explanation reports","api":"/api/explainability","ui_screen":"Evidence","test":"Phase 15–16 tests","evidence_artifact":"Explainability report","demo_step":"Open a report","limitation":"Explanations are descriptive, not causal or clinical."},
            {"requirement":"Prediction and decision support","feature":"Artifact-backed prediction, thresholds and risk bands","api":"/api/predictions","ui_screen":"Decision Center","test":"Phase 17 tests","evidence_artifact":"Prediction record","demo_step":"Predict a held-out sample","limitation":"Research output; not a diagnosis or validated risk score."},
            {"requirement":"Scalability and privacy","feature":"Limits, audit trail, file scanning and retention controls","api":"/api/platform/limits, /api/platform/audit/events","ui_screen":"Governance Center","test":"Phase 19 platform tests","evidence_artifact":"Audit events and scan response","demo_step":"Run a security scan","limitation":"Deployment authentication and organization policy remain required."},
            {"requirement":"Hardware readiness","feature":"Backend selection, compatibility and explicit unavailable states","api":"/api/platform/hardware/*","ui_screen":"Governance Center","test":"Hardware compatibility tests","evidence_artifact":"Compatibility response","demo_step":"Check simulator and hardware readiness","limitation":"No hardware job is claimed without provider credentials and job metadata."},
            {"requirement":"Final delivery","feature":"Validation matrix, documentation and demo flow","api":"/api/platform/validation/matrix","ui_screen":"Governance Center","test":"Phase 20 contract tests and CI","evidence_artifact":"SIH matrix and release checklist","demo_step":"Run the complete demonstration","limitation":"Licensed dataset and clean-machine reproducibility must be confirmed by the operator."},
        ]
        return ValidationMatrix(problem_id="26139", rows=rows, status="ready_for_demo")

    def readiness(self) -> PlatformReadiness:
        controls = {
            "bounded_uploads": True, "bounded_quantum_resources": True, "privacy_scan": True,
            "raw_data_logging_disabled": True, "audit_events": True, "environment_only_secrets": True,
            "hardware_explicit_states": True, "federated_metadata_only": True, "validation_matrix": True,
        }
        return PlatformReadiness(phase_19_status="ready", phase_20_status="ready", controls=controls, limitations=["Production authentication/RBAC must be supplied by the deployment environment.", "Real hardware queue, cost and calibration evidence requires an operator-configured provider job.", "Clinical validation and quantum advantage are not claimed."])
