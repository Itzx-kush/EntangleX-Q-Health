from __future__ import annotations
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, Field

class DatasetSummary(BaseModel):
    id: str
    name: str
    original_filename: str
    extension: str
    size_bytes: int
    sha256: str
    rows: int
    columns: int
    numeric_columns: list[str]
    categorical_columns: list[str]
    datetime_columns: list[str]
    missing_values: dict[str, int]
    total_missing_values: int
    duplicate_rows: int
    target_column: str | None = None
    class_distribution: dict[str, int] | None = None
    class_proportions: dict[str, float] | None = None
    class_count: int | None = None
    imbalance_ratio: float | None = None
    task_type: Literal["classification", "regression"] = "classification"
    target_min: float | None = None
    target_max: float | None = None
    target_mean: float | None = None
    target_std: float | None = None
    warnings: list[str] = Field(default_factory=list)
    created_at: datetime

class DatasetList(BaseModel):
    items: list[DatasetSummary]
    total: int

class TargetSelectionRequest(BaseModel):
    target_column: str = Field(min_length=1, max_length=255)
    task_type: Literal["classification", "regression"] = "classification"

class PreviewRequest(BaseModel):
    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=20, ge=1, le=100)

class DatasetPreview(BaseModel):
    dataset_id: str
    columns: list[str]
    rows: list[dict[str, Any]]
    offset: int
    limit: int
    total_rows: int
