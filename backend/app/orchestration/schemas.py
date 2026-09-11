from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

BiomedicalModality = Literal["ehr", "genomics", "medical_image"]
TrainingModelType = Literal["logistic_regression", "svm", "random_forest", "vqc", "qsvm", "qnn"]
TrainingStatus = Literal["queued", "running", "completed", "failed", "cancel_requested", "cancelled"]

class BiomedicalValidationRequest(BaseModel):
    modality: BiomedicalModality
    samples: int = Field(default=1, ge=1)
    columns: list[dict[str, Any]] | None = None
    features: int | None = Field(default=None, ge=1)
    feature_names: list[str] | None = None
    numeric: bool = True
    target_column: str | None = None
    representation: Literal["embedding", "engineered_features"] | None = None
    embedding_dim: int | None = Field(default=None, ge=1)

class BiomedicalValidationResult(BaseModel):
    modality: BiomedicalModality
    valid: bool
    normalized: dict[str, Any]
    warnings: list[str] = Field(default_factory=list)

class TrainingJobRequest(BaseModel):
    model_type: TrainingModelType
    modality: BiomedicalModality
    dataset_id: str | None = None
    preprocessing_run_id: str | None = None
    encoding_run_id: str | None = None
    model_parameters: dict[str, Any] = Field(default_factory=dict)
    seed: int = 42
    parent_job_id: str | None = None

    @model_validator(mode="after")
    def validate_prerequisites(self):
        if self.model_type in {"logistic_regression", "svm", "random_forest"} and not self.preprocessing_run_id:
            raise ValueError("preprocessing_run_id is required for classical training jobs")
        if self.model_type in {"vqc", "qsvm", "qnn"} and not self.encoding_run_id:
            raise ValueError("encoding_run_id is required for quantum training jobs")
        return self

class TrainingJobResponse(BaseModel):
    id: str
    model_type: TrainingModelType
    modality: BiomedicalModality
    dataset_id: str | None
    preprocessing_run_id: str | None
    encoding_run_id: str | None
    status: TrainingStatus
    progress: int = Field(ge=0, le=100)
    configuration: dict[str, Any]
    result: dict[str, Any] | None = None
    error: dict[str, Any] | None = None
    cancel_requested: bool
    parent_job_id: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None

class TrainingJobList(BaseModel):
    items: list[TrainingJobResponse]
    total: int
