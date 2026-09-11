from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ClassicalExplainabilityRequest(BaseModel):
    model_run_id: str = Field(min_length=1)
    evaluation_run_id: str | None = None
    sample_limit: int = Field(default=8, ge=1, le=32)
    top_k: int = Field(default=8, ge=1, le=32)
    thresholds: list[float] | None = None


class QuantumExplainabilityRequest(BaseModel):
    model_type: Literal["vqc", "qsvm", "qnn"]
    run_ids: list[str] = Field(min_length=1, max_length=8)
    sample_limit: int = Field(default=4, ge=1, le=16)
    top_k: int = Field(default=8, ge=1, le=32)
    feature_delta: float = Field(default=0.1, gt=0, le=1.0)
    parameter_delta: float = Field(default=0.1, gt=0, le=1.0)


class ExplainabilityReportListResponse(BaseModel):
    items: list[dict]
    total: int
