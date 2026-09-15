from __future__ import annotations
from typing import Any, Literal
from pydantic import BaseModel, Field, model_validator

ModelName = Literal["logistic_regression", "svm", "random_forest", "vqc", "qsvm", "qnn"]

class ControlledExperimentRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    preprocessing_run_id: str
    models: list[ModelName] = Field(min_length=1, max_length=6)
    model_parameters: dict[str, dict[str, Any]] = Field(default_factory=dict)
    quantum: dict[str, Any] = Field(default_factory=lambda: {"qubits": 4, "entanglement": "linear", "seed": 42})
    comparison_metric: str = "f1"
    parent_experiment_id: str | None = None

    @model_validator(mode="after")
    def validate_models(self):
        if len(set(self.models)) != len(self.models):
            raise ValueError("Each selected model may appear only once.")
        allowed = set(self.models)
        unknown = set(self.model_parameters) - allowed
        if unknown:
            raise ValueError(f"Parameters supplied for unselected models: {sorted(unknown)}")
        return self
