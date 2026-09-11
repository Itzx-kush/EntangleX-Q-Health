from __future__ import annotations

from pathlib import Path

import pytest

from app.benchmarking.errors import BenchmarkError
from app.benchmarking.repository import BenchmarkRepository
from app.benchmarking.schemas import BenchmarkCreateRequest, BenchmarkExperimentInput, FoldResult
from app.benchmarking.service import BenchmarkService
from app.experiments.registry import ExperimentRegistry
from app.experiments.repository import ExperimentRepository
from app.experiments.schemas import ExperimentCreateRequest


def build_services(tmp_path: Path):
    database_url = f"sqlite:///{tmp_path / 'benchmark.db'}"
    experiments = ExperimentRegistry(repository=ExperimentRepository(database_url), allowed_roots=[tmp_path])
    benchmarks = BenchmarkService(repository=BenchmarkRepository(database_url), experiments=experiments)
    first = experiments.register(ExperimentCreateRequest(name="SVM", task_type="classification", model_family="svm", modality="ehr", seed_snapshot={"split": 42}))
    second = experiments.register(ExperimentCreateRequest(name="SVM alt", task_type="classification", model_family="svm", modality="ehr", seed_snapshot={"split": 43}))
    return experiments, benchmarks, first, second


def folds():
    return [
        FoldResult(repeat=1, fold=1, labels=[0, 1, 1, 0], predictions=[0, 1, 0, 0], probabilities=[0.1, 0.8, 0.4, 0.2], train_metrics={"f1": 0.9}, train_size=8, validation_size=4, duration_seconds=1.2, resource_measurements={"training_seconds": 1.2, "circuit_depth": 4}),
        FoldResult(repeat=1, fold=2, labels=[0, 1, 1, 0], predictions=[0, 1, 1, 0], probabilities=[0.2, 0.7, 0.8, 0.1], train_metrics={"f1": 0.92}, train_size=8, validation_size=4, duration_seconds=1.4, resource_measurements={"training_seconds": 1.4, "circuit_depth": 4}),
    ]


def test_repeated_metrics_confidence_intervals_calibration_and_resources(tmp_path: Path):
    _, service, first, _ = build_services(tmp_path)
    result = service.create(BenchmarkCreateRequest(experiments=[BenchmarkExperimentInput(experiment_id=first["id"], fold_results=folds())], repeats=1, folds=2))
    report = result["report"]["experiments"][0]

    assert report["fold_count"] == 2
    assert report["metrics"]["f1"]["confidence_interval_95"] is not None
    assert "brier_score" in report["metrics"]
    assert "ece" in report["metrics"]
    assert report["generalization_gaps"]["f1"]["mean"] > 0
    assert report["resources"]["training_seconds"]["mean"] == pytest.approx(1.3)
    assert result["report"]["comparison"]["conclusion"] == "inconclusive"


def test_compatible_comparison_is_descriptive_and_missing_metrics_are_honest(tmp_path: Path):
    _, service, first, second = build_services(tmp_path)
    result = service.create(BenchmarkCreateRequest(experiments=[BenchmarkExperimentInput(experiment_id=first["id"], fold_results=folds()), BenchmarkExperimentInput(experiment_id=second["id"], fold_results=[FoldResult(repeat=1, fold=1, validation_metrics={"f1": 0.5}), FoldResult(repeat=1, fold=2, validation_metrics={"f1": 0.6})])]))

    assert result["report"]["comparison"]["conclusion"] in {"better", "worse", "comparable", "inconclusive"}
    assert "winner" not in str(result["report"]).lower()


def test_incompatible_experiments_are_rejected(tmp_path: Path):
    experiments, service, first, _ = build_services(tmp_path)
    other = experiments.register(ExperimentCreateRequest(name="QNN", task_type="classification", model_family="qnn", modality="ehr", seed_snapshot={"split": 44}))
    with pytest.raises(BenchmarkError) as error:
        service.create(BenchmarkCreateRequest(experiments=[BenchmarkExperimentInput(experiment_id=first["id"], fold_results=folds()), BenchmarkExperimentInput(experiment_id=other["id"], fold_results=folds())]))
    assert error.value.code == "INCOMPATIBLE_EXPERIMENTS"
