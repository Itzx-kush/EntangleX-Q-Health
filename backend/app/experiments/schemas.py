from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


ExperimentTaskType = Literal["classification", "regression"]
ExperimentStatus = Literal["registered", "running", "completed", "failed", "archived"]


class ArtifactInput(BaseModel):
    name: str = Field(min_length=1)
    kind: str = Field(min_length=1)
    reference: str = Field(min_length=1)
    path: str | None = None
    sha256: str | None = Field(default=None, pattern=r"^[0-9a-fA-F]{64}$")
    size_bytes: int | None = Field(default=None, ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ExperimentCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=4000)
    task_type: ExperimentTaskType
    model_family: str = Field(min_length=1, max_length=120)
    modality: str = Field(min_length=1, max_length=80)
    status: ExperimentStatus = "registered"
    configuration_snapshot: dict[str, Any] = Field(default_factory=dict)
    environment_snapshot: dict[str, Any] = Field(default_factory=dict)
    seed_snapshot: dict[str, Any] = Field(default_factory=dict)
    artifacts: list[ArtifactInput] = Field(default_factory=list)
    parent_experiment_id: str | None = None
    result_references: list[str] = Field(default_factory=list)
    recorded_results: dict[str, Any] = Field(default_factory=dict)
    dataset_card: dict[str, Any] | None = None
    model_card: dict[str, Any] | None = None
    scientific_warnings: list[str] = Field(default_factory=list)
    node_version: str | None = None
    git_commit: str | None = None


class CloneExperimentRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=4000)
    parameter_overrides: dict[str, Any] = Field(default_factory=dict)
    node_version: str | None = None
    git_commit: str | None = None


class ExperimentListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int


class CompareExperimentsRequest(BaseModel):
    experiment_ids: list[str] = Field(min_length=2, max_length=10)


class ExperimentResponse(BaseModel):
    id: str
    name: str
    description: str
    task_type: ExperimentTaskType
    model_family: str
    modality: str
    status: ExperimentStatus
    configuration_snapshot: dict[str, Any]
    environment_snapshot: dict[str, Any]
    seed_snapshot: dict[str, Any]
    artifacts: list[dict[str, Any]]
    parent_experiment_id: str | None
    result_references: list[str]
    recorded_results: dict[str, Any]
    dataset_card: dict[str, Any] | None
    model_card: dict[str, Any] | None
    scientific_warnings: list[str]
    integrity: dict[str, Any]
    created_at: datetime
    updated_at: datetime
