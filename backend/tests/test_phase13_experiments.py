from __future__ import annotations

import hashlib
import json
import tempfile
import zipfile
from pathlib import Path

import pytest

from app.experiments.errors import ExperimentError
from app.experiments.registry import ExperimentRegistry
from app.experiments.repository import ExperimentRepository
from app.experiments.schemas import ArtifactInput, CloneExperimentRequest, CompareExperimentsRequest, ExperimentCreateRequest


def build_registry(tmp_path: Path) -> ExperimentRegistry:
    repository = ExperimentRepository(f"sqlite:///{tmp_path / 'experiments.db'}")
    return ExperimentRegistry(repository=repository, allowed_roots=[tmp_path])


def make_request(path: Path | None = None, **overrides):
    artifacts = []
    if path:
        artifacts.append(ArtifactInput(name="dataset", kind="dataset", reference="dataset-1", path=str(path)))
    values = {
        "name": "Baseline experiment",
        "description": "A recorded research run",
        "task_type": "classification",
        "model_family": "svm",
        "modality": "ehr",
        "configuration_snapshot": {"regularization_c": 1.0, "split_seed": 42},
        "seed_snapshot": {"dataset_split": 42, "classical_model": 7, "nondeterministic_operations": []},
        "artifacts": artifacts,
        "recorded_results": {"f1": 0.81},
        "dataset_card": {"identity": "dataset-1", "sample_count": 40, "feature_count": 8, "limitations": ["Research use only"]},
        "model_card": {"model_type": "svm", "intended_use": "Research comparison", "limitations": ["Not a clinical diagnosis"]},
    }
    values.update(overrides)
    return ExperimentCreateRequest(**values)


def test_registration_captures_environment_seeds_and_checksum(tmp_path: Path):
    artifact = tmp_path / "dataset.csv"
    artifact.write_text("x,y\n1,0\n", encoding="utf-8")
    registry = build_registry(tmp_path)

    experiment = registry.register(make_request(artifact))

    expected = hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert experiment["artifacts"][0]["sha256"] == expected
    assert experiment["integrity"]["ready"] is True
    assert experiment["environment"]["python_version"]
    assert experiment["seeds"]["dataset_split"] == 42


def test_clone_is_immutable_and_preserves_parent_lineage(tmp_path: Path):
    registry = build_registry(tmp_path)
    source = registry.register(make_request())

    clone = registry.clone(source["id"], CloneExperimentRequest(parameter_overrides={"regularization_c": 2.0}))

    assert clone["id"] != source["id"]
    assert clone["parent_experiment_id"] == source["id"]
    assert clone["configuration"]["regularization_c"] == 2.0
    assert registry.get(source["id"])["configuration"]["regularization_c"] == 1.0


def test_tampered_artifact_blocks_clone(tmp_path: Path):
    artifact = tmp_path / "model.joblib"
    artifact.write_bytes(b"original")
    registry = build_registry(tmp_path)
    source = registry.register(make_request(artifact))
    artifact.write_bytes(b"altered")

    with pytest.raises(ExperimentError) as error:
        registry.clone(source["id"], CloneExperimentRequest())
    assert error.value.code == "ARTIFACT_INTEGRITY_FAILED"
    assert registry.get(source["id"])["integrity"]["status"] == "attention_required"


def test_compare_rejects_incompatible_experiments(tmp_path: Path):
    registry = build_registry(tmp_path)
    first = registry.register(make_request())
    second = registry.register(make_request(name="Regression", task_type="regression"))

    with pytest.raises(ExperimentError) as error:
        registry.compare([first["id"], second["id"]])
    assert error.value.code == "INCOMPATIBLE_EXPERIMENTS"


def test_compare_reports_real_results_without_winner(tmp_path: Path):
    registry = build_registry(tmp_path)
    first = registry.register(make_request())
    second = registry.register(make_request(name="Alternative", configuration_snapshot={"regularization_c": 2.0}, recorded_results={}))

    comparison = registry.compare([first["id"], second["id"]])

    assert comparison["compatible"] is True
    assert "configuration_differences" in comparison
    assert comparison["metrics"][0]["recorded_results"]["f1"] == 0.81
    assert comparison["metrics"][1]["missing_metrics"]
    assert "winner" not in json.dumps(comparison).lower()


def test_export_contains_structured_json_and_zip_evidence(tmp_path: Path):
    registry = build_registry(tmp_path)
    experiment = registry.register(make_request())

    payload = registry.export_payload(experiment["id"])
    archive = registry.export_zip(experiment["id"])

    assert payload["schema_version"] == "phase13.v1"
    with tempfile.TemporaryDirectory() as directory:
        archive_path = Path(directory) / "evidence.zip"
        archive_path.write_bytes(archive)
        with zipfile.ZipFile(archive_path) as bundle:
            assert set(bundle.namelist()) == {"experiment.json", "dataset-card.json", "model-card.json", "artifact-manifest.json"}


def test_reference_only_cards_are_honest(tmp_path: Path):
    registry = build_registry(tmp_path)
    experiment = registry.register(make_request(dataset_card=None, model_card=None))

    assert registry.dataset_card(experiment["id"])["status"] == "not_recorded"
    assert registry.model_card(experiment["id"])["status"] == "not_recorded"
