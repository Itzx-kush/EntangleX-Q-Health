from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, model_validator

class PredictionRequest(BaseModel):
    model_run_id: str = Field(min_length=1)
    features: list[float] | None = None
    sample_index: int | None = Field(default=None, ge=0)
    probability_threshold: float = Field(default=0.5, ge=0.0, le=1.0)
    low_risk_max: float = Field(default=0.33, ge=0.0, le=1.0)
    intermediate_risk_max: float = Field(default=0.66, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bands(self):
        if self.low_risk_max >= self.intermediate_risk_max:
            raise ValueError("low_risk_max must be smaller than intermediate_risk_max")
        return self

class PredictionRecord(BaseModel):
    id: str
    model_run_id: str
    model_type: str
    task_type: str
    input_source: str
    sample_index: int | None
    feature_count: int
    prediction: float | int | str
    probability: float | None
    threshold: float | None
    risk_band: str
    risk_band_boundaries: dict[str, float] | None
    decision: str
    uncertainty_status: str
    scientific_warnings: list[str]
    created_at: datetime

class PredictionList(BaseModel):
    items: list[PredictionRecord]
    total: int
