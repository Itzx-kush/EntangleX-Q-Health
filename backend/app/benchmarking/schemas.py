from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class FoldResult(BaseModel):
    repeat: int = Field(ge=1)
    fold: int = Field(ge=1)
    train_metrics: dict[str, float] = Field(default_factory=dict)
    validation_metrics: dict[str, float] = Field(default_factory=dict)
    labels: list[int] | None = None
    predictions: list[int] | None = None
    probabilities: list[float] | None = None
    train_size: int | None = Field(default=None, ge=1)
    validation_size: int | None = Field(default=None, ge=1)
    duration_seconds: float | None = Field(default=None, ge=0)
    resource_measurements: dict[str, float] = Field(default_factory=dict)


class BenchmarkExperimentInput(BaseModel):
    experiment_id: str = Field(min_length=1)
    fold_results: list[FoldResult] = Field(min_length=2)


class BenchmarkCreateRequest(BaseModel):
    experiments: list[BenchmarkExperimentInput] = Field(min_length=1, max_length=10)
    primary_metric: str = "f1"
    stratified: bool = True
    repeats: int = Field(default=1, ge=1)
    folds: int = Field(default=2, ge=2)
    calibration_bins: int = Field(default=10, ge=2, le=50)
    notes: list[str] = Field(default_factory=list)


class BenchmarkListResponse(BaseModel):
    items: list[dict[str, Any]]
    total: int
