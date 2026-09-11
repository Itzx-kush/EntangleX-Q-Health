from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, Query
from fastapi.responses import JSONResponse, Response

from app.experiments.registry import ExperimentRegistry
from app.experiments.schemas import (
    CloneExperimentRequest,
    CompareExperimentsRequest,
    ExperimentCreateRequest,
    ExperimentListResponse,
    ExperimentResponse,
)


router = APIRouter(prefix="/api/experiments", tags=["experiments"])
_registry: ExperimentRegistry | None = None


def get_registry() -> ExperimentRegistry:
    global _registry
    if _registry is None:
        _registry = ExperimentRegistry()
    return _registry


def _response(record: dict[str, Any]) -> dict[str, Any]:
    value = dict(record)
    value["configuration_snapshot"] = value.get("configuration", {})
    value["environment_snapshot"] = value.get("environment", {})
    value["seed_snapshot"] = value.get("seeds", {})
    return value


@router.post("", response_model=ExperimentResponse, status_code=201)
def register_experiment(payload: ExperimentCreateRequest, registry: ExperimentRegistry = Depends(get_registry)):
    return _response(registry.register(payload))


@router.get("", response_model=ExperimentListResponse)
def list_experiments(
    search: str | None = Query(default=None, max_length=120),
    status: str | None = None,
    task_type: str | None = None,
    model_family: str | None = None,
    modality: str | None = None,
    registry: ExperimentRegistry = Depends(get_registry),
):
    items = registry.list(search=search, status=status, task_type=task_type, model_family=model_family, modality=modality)
    return {"items": [_response(item) for item in items], "total": len(items)}


@router.post("/compare")
def compare_experiments(payload: CompareExperimentsRequest, registry: ExperimentRegistry = Depends(get_registry)):
    return registry.compare(payload.experiment_ids)


@router.get("/{experiment_id}", response_model=ExperimentResponse)
def get_experiment(experiment_id: str, registry: ExperimentRegistry = Depends(get_registry)):
    return _response(registry.get(experiment_id))


@router.post("/{experiment_id}/clone", response_model=ExperimentResponse, status_code=201)
def clone_experiment(experiment_id: str, payload: CloneExperimentRequest, registry: ExperimentRegistry = Depends(get_registry)):
    return _response(registry.clone(experiment_id, payload))


@router.get("/{experiment_id}/export")
def export_experiment(
    experiment_id: str,
    format: Literal["json", "zip"] = "json",
    registry: ExperimentRegistry = Depends(get_registry),
):
    if format == "zip":
        return Response(
            content=registry.export_zip(experiment_id),
            media_type="application/zip",
            headers={"Content-Disposition": f'attachment; filename="experiment-{experiment_id}.zip"'},
        )
    return JSONResponse(content=registry.export_payload(experiment_id))


@router.get("/{experiment_id}/dataset-card")
def get_dataset_card(experiment_id: str, registry: ExperimentRegistry = Depends(get_registry)):
    return registry.dataset_card(experiment_id)


@router.get("/{experiment_id}/model-card")
def get_model_card(experiment_id: str, registry: ExperimentRegistry = Depends(get_registry)):
    return registry.model_card(experiment_id)
