from __future__ import annotations
import tempfile
from pathlib import Path

import pytest

from app.biomedical.adapters import validate_modality
from app.orchestration.repository import TrainingJobRepository
from app.orchestration.schemas import BiomedicalValidationRequest, TrainingJobRequest
from app.orchestration.service import TrainingOrchestrationService


def test_ehr_adapter_normalizes_schema():
    result = validate_modality(BiomedicalValidationRequest(modality="ehr", samples=10, target_column="disease", columns=[{"name":"age","kind":"numeric"},{"name":"sex","kind":"categorical"},{"name":"disease","kind":"categorical"}]))
    assert result.valid is True
    assert result.normalized["feature_count"] == 2
    assert result.normalized["representation"] == "structured_tabular"


def test_genomics_adapter_warns_for_high_dimension():
    result = validate_modality(BiomedicalValidationRequest(modality="genomics", samples=20, features=100))
    assert result.valid is True
    assert result.normalized["representation"] == "numeric_feature_matrix"
    assert result.warnings


def test_image_adapter_rejects_raw_image():
    with pytest.raises(Exception) as exc:
        validate_modality(BiomedicalValidationRequest(modality="medical_image", samples=4, embedding_dim=512))
    assert exc.value.code == "RAW_IMAGE_NOT_SUPPORTED"


def test_image_adapter_accepts_embedding():
    result = validate_modality(BiomedicalValidationRequest(modality="medical_image", samples=4, embedding_dim=128, representation="embedding"))
    assert result.valid is True
    assert result.normalized["feature_count"] == 128


def test_job_repository_persists_lifecycle():
    with tempfile.TemporaryDirectory() as directory:
        db = Path(directory) / "jobs.db"
        repository = TrainingJobRepository(f"sqlite:///{db}")
        service = TrainingOrchestrationService(repository=repository)
        job = service.create(TrainingJobRequest(model_type="qnn", modality="ehr", encoding_run_id="encoding-1", dataset_id="dataset-1", model_parameters={"max_iterations": 2}))
        assert job["status"] == "queued"
        assert job["progress"] == 0
        repository.update(job["id"], status="running", progress=25)
        loaded = service.get(job["id"])
        assert loaded["status"] == "running"
        assert loaded["progress"] == 25


def test_job_requires_matching_model_prerequisite():
    with pytest.raises(ValueError):
        TrainingJobRequest(model_type="qsvm", modality="genomics", preprocessing_run_id="prep-1")
    with pytest.raises(ValueError):
        TrainingJobRequest(model_type="random_forest", modality="ehr", encoding_run_id="encoding-1")
