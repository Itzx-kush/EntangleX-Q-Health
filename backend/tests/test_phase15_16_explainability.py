from __future__ import annotations

from pathlib import Path

from app.explainability.repository import ExplainabilityRepository
from app.explainability.service import calibration_summary, summarize_stability


def test_calibration_summary_is_measured_only_for_probability_scores():
    result = calibration_summary(__import__('numpy').array([0, 1, 1, 0]), __import__('numpy').array([0.1, 0.8, 0.7, 0.2]))

    assert result["status"] == "measured"
    assert result["brier_score"] >= 0
    assert 0 <= result["ece"] <= 1
    assert result["bins"]
    assert calibration_summary(__import__('numpy').array([0, 1]), __import__('numpy').array([2.0, -1.0]))["status"] == "unavailable"


def test_stability_reports_intervals_only_for_real_replicates():
    single = summarize_stability([{"summary": {"metrics": {"f1": 0.8}}}])
    multiple = summarize_stability([{"summary": {"metrics": {"f1": 0.8}}}, {"summary": {"metrics": {"f1": 0.9}}}])

    assert single["status"] == "insufficient_replicates"
    assert single["metrics"]["f1"]["confidence_interval_95"] is None
    assert multiple["status"] == "measured_replicates"
    assert multiple["metrics"]["f1"]["confidence_interval_95"] is not None


def test_explainability_reports_persist(tmp_path: Path):
    repository = ExplainabilityRepository(f"sqlite:///{tmp_path / 'reports.db'}")
    record = {"id": "report-1", "phase": "15", "target_type": "classical", "run_id": "model-1", "payload": {"status": "measured"}, "created_at": "2026-01-01T00:00:00+00:00"}
    repository.create(record)

    assert repository.get("report-1")["payload"]["status"] == "measured"
    assert repository.list("15")[0]["id"] == "report-1"
