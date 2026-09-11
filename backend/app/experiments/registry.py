from __future__ import annotations

import hashlib
import importlib.metadata
import io
import json
import os
import platform
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from app.core.config import settings
from app.experiments.errors import ExperimentError
from app.experiments.repository import ExperimentRepository
from app.experiments.schemas import ArtifactInput, CloneExperimentRequest, ExperimentCreateRequest


_PACKAGE_NAMES = (
    "fastapi", "pydantic", "numpy", "pandas", "scikit-learn", "joblib",
    "qiskit", "qiskit-aer", "sqlalchemy", "imbalanced-learn",
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def capture_environment(node_version: str | None = None, git_commit: str | None = None) -> dict[str, Any]:
    packages: dict[str, str | None] = {}
    for name in _PACKAGE_NAMES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python_version": platform.python_version(),
        "node_version": node_version or os.getenv("NODE_VERSION"),
        "operating_system": platform.system(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "application_version": settings.app_version,
        "git_commit": git_commit or os.getenv("ENTANGLEX_GIT_COMMIT"),
        "packages": packages,
        "captured_at": _now(),
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class ExperimentRegistry:
    def __init__(self, repository: ExperimentRepository | None = None, allowed_roots: Iterable[Path] | None = None):
        self.repository = repository or ExperimentRepository()
        roots = list(allowed_roots or [])
        roots.extend([Path.cwd(), settings.upload_dir, settings.model_dir, settings.experiment_dir])
        self.allowed_roots = tuple({root.resolve() for root in roots})

    def register(self, request: ExperimentCreateRequest) -> dict[str, Any]:
        if request.parent_experiment_id and not self.repository.get(request.parent_experiment_id):
            raise ExperimentError("PARENT_EXPERIMENT_NOT_FOUND", "The parent experiment was not found.", {"parent_experiment_id": request.parent_experiment_id}, 404)
        artifacts = self._normalize_artifacts(request.artifacts)
        warnings = list(request.scientific_warnings)
        if not request.seed_snapshot:
            warnings.append("Seed values were not supplied for this registration; determinism is not established.")
        if not request.recorded_results:
            warnings.append("No measured results were recorded for this experiment.")
        record = {
            "id": str(uuid.uuid4()),
            "name": request.name,
            "description": request.description,
            "task_type": request.task_type,
            "model_family": request.model_family,
            "modality": request.modality,
            "status": request.status,
            "configuration": dict(request.configuration_snapshot),
            "environment": {**capture_environment(request.node_version, request.git_commit), **request.environment_snapshot},
            "seeds": dict(request.seed_snapshot),
            "artifacts": artifacts,
            "parent_experiment_id": request.parent_experiment_id,
            "result_references": list(request.result_references),
            "recorded_results": dict(request.recorded_results),
            "dataset_card": request.dataset_card,
            "model_card": request.model_card,
            "scientific_warnings": list(dict.fromkeys(warnings)),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.repository.create(record)
        return self.get(record["id"])

    def get(self, experiment_id: str) -> dict[str, Any]:
        record = self.repository.get(experiment_id)
        if not record:
            raise ExperimentError("EXPERIMENT_NOT_FOUND", "The experiment was not found.", {"experiment_id": experiment_id}, 404)
        record["integrity"] = self._integrity(record["artifacts"])
        return record

    def list(self, **filters: str | None) -> list[dict[str, Any]]:
        return [self._with_integrity(record) for record in self.repository.list(**filters)]

    def clone(self, experiment_id: str, request: CloneExperimentRequest) -> dict[str, Any]:
        source = self.repository.get(experiment_id)
        if not source:
            raise ExperimentError("EXPERIMENT_NOT_FOUND", "The experiment was not found.", {"experiment_id": experiment_id}, 404)
        integrity = self._integrity(source["artifacts"])
        blocking = [item for item in integrity["artifacts"] if item["status"] in {"missing", "modified", "invalid_path"}]
        if blocking:
            raise ExperimentError("ARTIFACT_INTEGRITY_FAILED", "The source experiment contains missing or altered artifacts and cannot be cloned.", {"artifacts": blocking}, 409)
        configuration = dict(source["configuration"])
        configuration.update(request.parameter_overrides)
        warnings = list(source["scientific_warnings"])
        if any(item["status"] == "unverified" for item in integrity["artifacts"]):
            warnings.append("One or more source artifacts were reference-only and could not be checksum-verified during cloning.")
        clone_request = ExperimentCreateRequest(
            name=request.name or f"Clone of {source['name']}",
            description=request.description if request.description is not None else source["description"],
            task_type=source["task_type"], model_family=source["model_family"], modality=source["modality"],
            status="registered", configuration_snapshot=configuration,
            environment_snapshot={"cloned_from": experiment_id}, seed_snapshot=dict(source["seeds"]),
            artifacts=[ArtifactInput(**item) for item in source["artifacts"]],
            parent_experiment_id=experiment_id, result_references=list(source["result_references"]),
            recorded_results=dict(source["recorded_results"]), dataset_card=source["dataset_card"],
            model_card=source["model_card"], scientific_warnings=warnings,
            node_version=request.node_version, git_commit=request.git_commit,
        )
        return self.register(clone_request)

    def compare(self, experiment_ids: list[str]) -> dict[str, Any]:
        records = [self._require_raw(experiment_id) for experiment_id in experiment_ids]
        signatures = {(record["task_type"], record["model_family"], record["modality"]) for record in records}
        if len(signatures) != 1:
            raise ExperimentError(
                "INCOMPATIBLE_EXPERIMENTS",
                "Only experiments with the same task type, model family and modality can be compared.",
                {"experiment_ids": experiment_ids}, 409,
            )
        return {
            "compatible": True,
            "experiments": [{"id": record["id"], "name": record["name"], "status": record["status"]} for record in records],
            "configuration_differences": self._differences(records, "configuration"),
            "lineage_differences": self._lineage_differences(records),
            "metrics": [
                {
                    "experiment_id": record["id"],
                    "recorded_results": record["recorded_results"],
                    "missing_metrics": [] if record["recorded_results"] else ["No metrics were recorded for this experiment."],
                }
                for record in records
            ],
            "scientific_note": "This comparison is descriptive only; it does not select a winner or establish quantum advantage.",
        }

    def dataset_card(self, experiment_id: str) -> dict[str, Any]:
        record = self._require_raw(experiment_id)
        return record["dataset_card"] or {
            "status": "not_recorded",
            "experiment_id": experiment_id,
            "message": "No dataset card was supplied for this experiment; provenance and counts are unavailable.",
        }

    def model_card(self, experiment_id: str) -> dict[str, Any]:
        record = self._require_raw(experiment_id)
        return record["model_card"] or {
            "status": "not_recorded",
            "experiment_id": experiment_id,
            "message": "No model card was supplied for this experiment; intended use and limitations are unavailable.",
        }

    def export_payload(self, experiment_id: str) -> dict[str, Any]:
        record = self.get(experiment_id)
        return {
            "schema_version": "phase13.v1",
            "exported_at": _now(),
            "experiment": record,
            "dataset_card": self.dataset_card(experiment_id),
            "model_card": self.model_card(experiment_id),
            "artifact_manifest": record["artifacts"],
        }

    def export_zip(self, experiment_id: str) -> bytes:
        payload = self.export_payload(experiment_id)
        output = io.BytesIO()
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as bundle:
            bundle.writestr("experiment.json", json.dumps(payload["experiment"], indent=2, sort_keys=True))
            bundle.writestr("dataset-card.json", json.dumps(payload["dataset_card"], indent=2, sort_keys=True))
            bundle.writestr("model-card.json", json.dumps(payload["model_card"], indent=2, sort_keys=True))
            bundle.writestr("artifact-manifest.json", json.dumps(payload["artifact_manifest"], indent=2, sort_keys=True))
        return output.getvalue()

    def _require_raw(self, experiment_id: str) -> dict[str, Any]:
        record = self.repository.get(experiment_id)
        if not record:
            raise ExperimentError("EXPERIMENT_NOT_FOUND", "The experiment was not found.", {"experiment_id": experiment_id}, 404)
        return record

    def _with_integrity(self, record: dict[str, Any]) -> dict[str, Any]:
        record["integrity"] = self._integrity(record["artifacts"])
        return record

    def _normalize_artifacts(self, artifacts: list[ArtifactInput]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for artifact in artifacts:
            value = artifact.model_dump()
            if artifact.path:
                path = self._resolve_path(artifact.path)
                if not path.is_file():
                    raise ExperimentError("ARTIFACT_MISSING", "The declared artifact file does not exist.", {"path": artifact.path}, 422)
                actual = sha256_file(path)
                if artifact.sha256 and artifact.sha256.lower() != actual:
                    raise ExperimentError("ARTIFACT_CHECKSUM_MISMATCH", "The declared artifact checksum does not match the file.", {"path": artifact.path, "expected": artifact.sha256, "actual": actual}, 422)
                value["sha256"] = actual
                value["size_bytes"] = path.stat().st_size
                value["integrity_at_registration"] = "verified"
            else:
                value["integrity_at_registration"] = "unverified"
            normalized.append(value)
        return normalized

    def _resolve_path(self, raw_path: str) -> Path:
        path = Path(raw_path)
        resolved = (path if path.is_absolute() else Path.cwd() / path).resolve()
        if not any(self._within(resolved, root) for root in self.allowed_roots):
            raise ExperimentError("ARTIFACT_PATH_NOT_ALLOWED", "Artifact paths must remain inside an approved application directory.", {"path": raw_path}, 422)
        return resolved

    @staticmethod
    def _within(path: Path, root: Path) -> bool:
        try:
            path.relative_to(root)
            return True
        except ValueError:
            return False

    def _integrity(self, artifacts: list[dict[str, Any]]) -> dict[str, Any]:
        results: list[dict[str, Any]] = []
        for artifact in artifacts:
            result = {"name": artifact["name"], "kind": artifact["kind"], "reference": artifact["reference"], "status": "unverified"}
            if artifact.get("path"):
                try:
                    path = self._resolve_path(artifact["path"])
                    if not path.is_file():
                        result["status"] = "missing"
                    else:
                        actual = sha256_file(path)
                        result["status"] = "verified" if actual == artifact.get("sha256") else "modified"
                        result["actual_sha256"] = actual
                except ExperimentError:
                    result["status"] = "invalid_path"
            results.append(result)
        statuses = {item["status"] for item in results}
        ready = bool(results) and statuses == {"verified"}
        return {"ready": ready, "status": "verified" if ready else ("unverified" if not results or statuses == {"unverified"} else "attention_required"), "artifacts": results}

    @staticmethod
    def _differences(records: list[dict[str, Any]], field: str) -> dict[str, list[dict[str, Any]]]:
        keys = set().union(*(record[field].keys() for record in records))
        return {
            key: [{"experiment_id": record["id"], "value": record[field].get(key)} for record in records]
            for key in sorted(keys)
            if len({json.dumps(record[field].get(key), sort_keys=True, default=str) for record in records}) > 1
        }

    @staticmethod
    def _lineage_differences(records: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        return {
            "artifacts": [
                {"experiment_id": record["id"], "artifacts": [{"kind": item["kind"], "reference": item["reference"], "sha256": item.get("sha256")} for item in record["artifacts"]]}
                for record in records
            ],
            "parent_experiment_id": [
                {"experiment_id": record["id"], "value": record["parent_experiment_id"]} for record in records
            ],
        }
