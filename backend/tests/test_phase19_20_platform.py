from __future__ import annotations
from app.platform.schemas import FederatedSandboxRequest, FederatedSite, HardwareCompatibilityRequest, SecurityScanRequest
from app.platform.service import PlatformGovernanceService

def test_security_scan_flags_phi_without_retaining_values(tmp_path):
    service = PlatformGovernanceService(f"sqlite:///{tmp_path / 'platform.db'}")
    result = service.scan_security(SecurityScanRequest(file_name="patients.csv", content_type="text/csv", size_bytes=120, column_names=["patient_name", "age", "email"], sample_values={"email": "person@example.test"}))
    assert not result.raw_values_retained
    assert result.deidentification_required
    assert "PHI_OR_PII_LIKE_COLUMN_NAMES_DETECTED" in result.findings
    assert "person@example.test" not in result.model_dump_json()

def test_federated_sandbox_only_returns_weighted_parameters(tmp_path):
    service = PlatformGovernanceService(f"sqlite:///{tmp_path / 'platform.db'}")
    result = service.federated_sandbox(FederatedSandboxRequest(sites=[
        FederatedSite(site_id="hospital-a", sample_count=3, feature_count=2, parameter_vector=[1.0, 2.0]),
        FederatedSite(site_id="hospital-b", sample_count=1, feature_count=2, parameter_vector=[5.0, 6.0]),
    ], rounds=2))
    assert result.aggregated_parameters == [2.0, 3.0]
    assert result.raw_records_transferred is False
    assert all("parameter_vector" not in site for site in result.site_metadata)

def test_hardware_readiness_is_explicit_without_provider_token(tmp_path, monkeypatch):
    monkeypatch.delenv("IBM_QUANTUM_TOKEN", raising=False)
    monkeypatch.delenv("QISKIT_IBM_TOKEN", raising=False)
    service = PlatformGovernanceService(f"sqlite:///{tmp_path / 'platform.db'}")
    result = service.hardware_compatibility(HardwareCompatibilityRequest(backend_name="ibm_brisbane", qubits=4, shots=1024))
    assert result.compatible is False
    assert result.execution_mode == "unavailable"
    assert result.evidence_status == "unavailable"

def test_validation_matrix_and_limits_are_present(tmp_path):
    service = PlatformGovernanceService(f"sqlite:///{tmp_path / 'platform.db'}")
    assert service.limits().max_batch_predictions > 0
    matrix = service.validation_matrix()
    assert matrix.problem_id == "26139"
    assert matrix.status == "ready_for_demo"
    assert len(matrix.rows) >= 8
