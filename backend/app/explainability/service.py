from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import joblib
import numpy as np
from sklearn.inspection import permutation_importance

from app.core.config import settings
from app.evaluation.metrics import evaluate_binary, model_scores
from app.evaluation.repository import EvaluationRepository
from app.explainability.errors import ExplainabilityError
from app.explainability.repository import ExplainabilityRepository
from app.explainability.schemas import ClassicalExplainabilityRequest, QuantumExplainabilityRequest
from app.ml.repository import ModelRepository
from app.quantum.model_utils import feature_states, fidelity_kernel
from app.quantum.qml_repository import QMLRepository
from app.quantum.qnn import QNNService
from app.quantum.vqc import VQCService


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and np.isfinite(float(value))


def calibration_summary(labels: np.ndarray, probabilities: np.ndarray, bins: int = 10) -> dict[str, Any]:
    labels = np.asarray(labels, dtype=float)
    probabilities = np.asarray(probabilities, dtype=float)
    if not len(labels) or len(labels) != len(probabilities) or np.any(probabilities < 0) or np.any(probabilities > 1):
        return {"status": "unavailable", "reason": "Probability scores in [0, 1] are required for calibration."}
    brier = float(np.mean((probabilities - labels) ** 2))
    edges = np.linspace(0.0, 1.0, bins + 1)
    ece = 0.0
    bin_rows: list[dict[str, Any]] = []
    for index in range(bins):
        mask = (probabilities >= edges[index]) & (probabilities <= edges[index + 1] if index == bins - 1 else probabilities < edges[index + 1])
        count = int(mask.sum())
        if not count:
            continue
        confidence = float(probabilities[mask].mean())
        observed = float(labels[mask].mean())
        ece += count / len(labels) * abs(confidence - observed)
        bin_rows.append({"bin": index, "count": count, "mean_probability": confidence, "observed_rate": observed})
    return {"status": "measured", "brier_score": brier, "ece": float(ece), "bins": bin_rows}


def summarize_stability(records: list[dict[str, Any]]) -> dict[str, Any]:
    metrics: dict[str, list[float]] = {}
    for record in records:
        for key, value in record.get("summary", {}).get("metrics", {}).items():
            if _numeric(value):
                metrics.setdefault(key, []).append(float(value))
    summaries: dict[str, Any] = {}
    for key, values in sorted(metrics.items()):
        array = np.asarray(values, dtype=float)
        mean = float(array.mean())
        standard_deviation = float(array.std(ddof=1)) if len(array) > 1 else 0.0
        interval = None if len(array) < 2 else [float(mean - 1.96 * standard_deviation / np.sqrt(len(array))), float(mean + 1.96 * standard_deviation / np.sqrt(len(array)))]
        summaries[key] = {"count": len(values), "mean": mean, "standard_deviation": standard_deviation, "confidence_interval_95": interval, "values": [float(value) for value in values]}
    return {"status": "measured_replicates" if len(records) > 1 else "insufficient_replicates", "run_count": len(records), "metrics": summaries, "message": "Intervals are computed only from the supplied persisted runs; a single run cannot establish stability." if len(records) < 2 else "Run-to-run stability is descriptive and does not establish clinical reliability."}


class ExplainabilityService:
    def __init__(self, repository: ExplainabilityRepository | None = None, models: ModelRepository | None = None, evaluations: EvaluationRepository | None = None, quantum_runs: QMLRepository | None = None):
        self.repository = repository or ExplainabilityRepository()
        self.models = models or ModelRepository()
        self.evaluations = evaluations or EvaluationRepository()
        self.quantum_runs = quantum_runs or QMLRepository()

    def create_classical(self, request: ClassicalExplainabilityRequest) -> dict[str, Any]:
        record = self.models.get(request.model_run_id)
        if not record:
            raise ExplainabilityError("MODEL_RUN_NOT_FOUND", "Model run was not found.", request.model_run_id, 404)
        evaluation = self.evaluations.get(request.evaluation_run_id) if request.evaluation_run_id else None
        if request.evaluation_run_id and not evaluation:
            raise ExplainabilityError("EVALUATION_RUN_NOT_FOUND", "Evaluation run was not found.", request.evaluation_run_id, 404)
        artifact_path = settings.model_dir / "classical" / Path(record["artifact_path"]).name
        if not artifact_path.exists():
            raise ExplainabilityError("MODEL_ARTIFACT_MISSING", "The model artifact is unavailable for explanation.", str(artifact_path), 404)
        bundle = joblib.load(artifact_path)
        required = {"model", "test_features", "test_labels"}
        if not required.issubset(bundle):
            raise ExplainabilityError("MODEL_ARTIFACT_INCOMPATIBLE", "The model artifact does not contain the held-out features and labels required for explanation.")
        model = bundle["model"]
        features = np.asarray(bundle["test_features"], dtype=float)
        labels = np.asarray(bundle["test_labels"])
        if features.ndim != 2 or len(features) != len(labels):
            raise ExplainabilityError("INVALID_EXPLANATION_MATRIX", "The held-out feature matrix and labels are inconsistent.")
        names = list(bundle.get("feature_names", []))
        if len(names) != features.shape[1]:
            names = [f"feature_{index + 1}" for index in range(features.shape[1])]
        scores = model_scores(model, features)
        predictions = np.asarray(model.predict(features))
        importance, method, direction = self._importance(model, features, labels, names)
        order = np.argsort(-np.abs(importance))
        top_indices = order[: min(request.top_k, len(order))]
        top_features = [{"rank": index + 1, "feature": names[feature_index], "source_feature": names[feature_index], "importance": float(importance[feature_index]), "absolute_importance": float(abs(importance[feature_index])), "direction": float(direction[feature_index]), "provenance": "feature name from the persisted preprocessing/model artifact"} for index, feature_index in enumerate(top_indices)]
        local = self._local_explanations(model, features, names, top_indices, request.sample_limit)
        thresholds = self._threshold_analysis(labels, scores, request.thresholds)
        payload = {
            "phase": 15,
            "report_type": "classical_explainability",
            "model_run_id": request.model_run_id,
            "evaluation_run_id": request.evaluation_run_id,
            "model_type": record["model_type"],
            "dataset_id": record["dataset_id"],
            "sample_count": int(len(features)),
            "feature_count": int(features.shape[1]),
            "importance_method": method,
            "global_importance": top_features,
            "local_explanations": local,
            "calibration": calibration_summary(labels, scores) if scores is not None else {"status": "unavailable", "reason": "The persisted model does not expose probability scores."},
            "threshold_analysis": thresholds,
            "evaluation_reference": evaluation["id"] if evaluation else None,
            "scientific_warnings": ["Feature importance describes model association, not biological causation.", "Explanations are valid only for this persisted model, preprocessing artifact and held-out sample.", "Calibration and thresholds are descriptive unless validated on an appropriate external cohort."],
        }
        return self._save("15", "classical", request.model_run_id, payload)

    def create_quantum(self, request: QuantumExplainabilityRequest) -> dict[str, Any]:
        records = [self._quantum_record(request.model_type, run_id) for run_id in request.run_ids]
        primary = records[0]
        encoding = self.quantum_runs.get_encoding(primary["encoding_run_id"])
        if not encoding:
            raise ExplainabilityError("ENCODING_RUN_NOT_FOUND", "The quantum encoding run was not found.", primary["encoding_run_id"], 404)
        encoding_path = settings.model_dir / "quantum_encoding" / Path(encoding["artifact_path"]).name
        if not encoding_path.exists():
            raise ExplainabilityError("ENCODING_ARTIFACT_MISSING", "The quantum encoding artifact is unavailable.", str(encoding_path), 404)
        encoded = np.load(encoding_path)
        test_features = np.asarray(encoded["test_features"], dtype=float)
        train_features = np.asarray(encoded["train_features"], dtype=float)
        names = list(encoding.get("summary", {}).get("feature_names", []))
        if len(names) != test_features.shape[1]:
            names = [f"encoded_feature_{index + 1}" for index in range(test_features.shape[1])]
        artifact = self._load_quantum_artifact(request.model_type, primary)
        entanglement = encoding["configuration"]["entanglement"]
        sample_rows = test_features[: request.sample_limit]
        base_scores = [self._quantum_score(request.model_type, primary, encoding, artifact, row, entanglement) for row in sample_rows]
        feature_sensitivity = self._feature_sensitivity(request.model_type, primary, encoding, artifact, sample_rows, train_features.mean(axis=0), names, entanglement, request.feature_delta, request.top_k)
        parameter_sensitivity = self._parameter_sensitivity(request.model_type, primary, encoding, artifact, sample_rows[0] if len(sample_rows) else train_features[0], entanglement, request.parameter_delta, request.top_k)
        stability = summarize_stability(records)
        uncertainty = {"status": stability["status"], "source": "real persisted quantum run summaries", "metrics": stability["metrics"]}
        payload = {
            "phase": 16,
            "report_type": "quantum_explainability",
            "model_type": request.model_type,
            "run_ids": request.run_ids,
            "primary_run_id": primary["id"],
            "encoding_run_id": primary["encoding_run_id"],
            "dataset_id": primary["dataset_id"],
            "circuit_resources": {key: primary.get("summary", {}).get(key) for key in ("circuit_depth", "circuit_size", "operation_counts", "parameter_count")},
            "sample_count": int(len(sample_rows)),
            "baseline_scores": [float(score) for score in base_scores],
            "feature_sensitivity": feature_sensitivity,
            "parameter_sensitivity": parameter_sensitivity,
            "seed_stability": stability,
            "uncertainty": uncertainty,
            "noise_stability": {"status": "not_measured", "message": "No noisy-simulator or hardware run was supplied. Ideal-state results are not relabeled as noise robustness."},
            "scientific_warnings": ["Quantum sensitivity is a descriptive perturbation analysis, not a causal interpretation.", "Stability intervals require multiple persisted runs with compatible configurations.", "Noise and hardware robustness remain unmeasured until real noisy-simulator or hardware records are supplied.", "No quantum advantage or clinical claim is inferred from this report."],
        }
        return self._save("16", "quantum", primary["id"], payload)

    def get(self, report_id: str) -> dict[str, Any]:
        record = self.repository.get(report_id)
        if not record:
            raise ExplainabilityError("EXPLAINABILITY_REPORT_NOT_FOUND", "The explainability report was not found.", report_id, 404)
        return record

    def list(self, phase: str | None = None) -> list[dict[str, Any]]:
        return self.repository.list(phase)

    def _save(self, phase: str, target_type: str, run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        record = {"id": str(uuid.uuid4()), "phase": phase, "target_type": target_type, "run_id": run_id, "payload": payload, "created_at": _now()}
        self.repository.create(record)
        return record

    @staticmethod
    def _importance(model: Any, features: np.ndarray, labels: np.ndarray, names: list[str]) -> tuple[np.ndarray, str, np.ndarray]:
        if hasattr(model, "coef_"):
            coefficients = np.asarray(model.coef_, dtype=float)
            direction = coefficients.mean(axis=0) if coefficients.ndim > 1 else coefficients
            return np.abs(coefficients).mean(axis=0), "model_coefficients", direction
        if hasattr(model, "feature_importances_"):
            values = np.asarray(model.feature_importances_, dtype=float)
            return values, "tree_feature_importances", values
        try:
            result = permutation_importance(model, features, labels, n_repeats=3, random_state=42, scoring="f1")
            return np.asarray(result.importances_mean, dtype=float), "permutation_f1", np.asarray(result.importances_mean, dtype=float)
        except Exception:
            return np.zeros(len(names), dtype=float), "unavailable", np.zeros(len(names), dtype=float)

    @staticmethod
    def _score(model: Any, features: np.ndarray) -> np.ndarray | None:
        if hasattr(model, "predict_proba"):
            probabilities = np.asarray(model.predict_proba(features))
            classes = np.asarray(getattr(model, "classes_", [0, 1]))
            index = int(np.flatnonzero(classes == 1)[0]) if np.any(classes == 1) else probabilities.shape[1] - 1
            return probabilities[:, index].astype(float)
        if hasattr(model, "decision_function"):
            return np.asarray(model.decision_function(features), dtype=float).reshape(-1)
        return None

    def _local_explanations(self, model: Any, features: np.ndarray, names: list[str], indices: np.ndarray, limit: int) -> list[dict[str, Any]]:
        baseline = features.mean(axis=0)
        rows: list[dict[str, Any]] = []
        for sample_index, row in enumerate(features[:limit]):
            base_value = self._score(model, np.asarray([row]))
            if base_value is None:
                continue
            contributions = []
            for feature_index in indices:
                changed = row.copy()
                changed[feature_index] = baseline[feature_index]
                changed_value = self._score(model, np.asarray([changed]))
                if changed_value is not None:
                    contributions.append({"feature": names[feature_index], "value": float(row[feature_index]), "baseline_value": float(baseline[feature_index]), "contribution": float(base_value[0] - changed_value[0])})
            rows.append({"sample_index": sample_index, "base_score": float(base_value[0]), "top_contributions": contributions})
        return rows

    @staticmethod
    def _threshold_analysis(labels: np.ndarray, scores: np.ndarray | None, requested: list[float] | None) -> dict[str, Any]:
        if scores is None or np.any(scores < 0) or np.any(scores > 1):
            return {"status": "unavailable", "reason": "Threshold analysis requires probability scores in [0, 1].", "thresholds": []}
        thresholds = requested or [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8]
        rows = []
        for threshold in thresholds:
            if not 0 < threshold < 1:
                continue
            metrics = evaluate_binary(labels, (scores >= threshold).astype(int), scores)
            rows.append({"threshold": float(threshold), "sensitivity": metrics["sensitivity"], "specificity": metrics["specificity"], "precision": metrics["precision"], "f1": metrics["f1"], "false_negative_rate": float(1.0 - metrics["sensitivity"])})
        return {"status": "measured", "thresholds": rows, "selection_note": "No threshold is selected automatically; the trade-off must be reviewed for the intended research use."}

    def _quantum_record(self, model_type: str, run_id: str) -> dict[str, Any]:
        record = self.quantum_runs.get_vqc(run_id) if model_type == "vqc" else self.quantum_runs.get_model(run_id, model_type)
        if not record:
            raise ExplainabilityError("QUANTUM_RUN_NOT_FOUND", "The quantum model run was not found.", run_id, 404)
        return record

    @staticmethod
    def _load_quantum_artifact(model_type: str, record: dict[str, Any]):
        directory = {"vqc": "vqc", "qsvm": "qsvm", "qnn": "qnn"}[model_type]
        path = settings.model_dir / directory / Path(record["artifact_path"]).name
        if not path.exists():
            raise ExplainabilityError("QUANTUM_ARTIFACT_MISSING", "The quantum model artifact is unavailable.", str(path), 404)
        return joblib.load(path) if model_type == "qsvm" else np.load(path)

    @staticmethod
    def _quantum_score(model_type: str, record: dict[str, Any], encoding: dict[str, Any], artifact: Any, row: np.ndarray, entanglement: str) -> float:
        config = record["configuration"]
        if model_type == "vqc":
            return float(VQCService.probability(row, np.asarray(artifact["parameters"]), config["ansatz_reps"], entanglement))
        if model_type == "qnn":
            parameters = np.asarray(artifact["parameters"])
            value = QNNService.raw_prediction(row, parameters, config["ansatz_reps"], entanglement)
            return float(QNNService.sigmoid(np.asarray([value]))[0]) if record["task_type"] == "classification" else float(value)
        states = feature_states(np.asarray([row]), entanglement)
        kernel = fidelity_kernel(states, artifact["training_states"])
        model = artifact["model"]
        probabilities = np.asarray(model.predict_proba(kernel))
        classes = np.asarray(model.classes_)
        index = int(np.flatnonzero(classes == 1)[0]) if np.any(classes == 1) else probabilities.shape[1] - 1
        return float(probabilities[0, index])

    def _feature_sensitivity(self, model_type: str, record: dict[str, Any], encoding: dict[str, Any], artifact: Any, rows: np.ndarray, baseline: np.ndarray, names: list[str], entanglement: str, delta: float, top_k: int) -> list[dict[str, Any]]:
        values = []
        for feature_index, name in enumerate(names[: min(top_k, len(names))]):
            changes = []
            for row in rows:
                plus = row.copy(); minus = row.copy()
                plus[feature_index] = np.clip(plus[feature_index] + delta, 0.0, np.pi)
                minus[feature_index] = np.clip(minus[feature_index] - delta, 0.0, np.pi)
                base = self._quantum_score(model_type, record, encoding, artifact, row, entanglement)
                plus_value = self._quantum_score(model_type, record, encoding, artifact, plus, entanglement)
                minus_value = self._quantum_score(model_type, record, encoding, artifact, minus, entanglement)
                changes.append({"sample_delta": float((plus_value - minus_value) / 2.0), "baseline": float(base), "training_mean": float(baseline[feature_index])})
            magnitude = float(np.mean([abs(item["sample_delta"]) for item in changes])) if changes else 0.0
            values.append({"feature": name, "mean_absolute_sensitivity": magnitude, "observations": changes})
        return sorted(values, key=lambda item: -item["mean_absolute_sensitivity"])

    def _parameter_sensitivity(self, model_type: str, record: dict[str, Any], encoding: dict[str, Any], artifact: Any, row: np.ndarray, entanglement: str, delta: float, top_k: int) -> dict[str, Any]:
        if model_type == "qsvm":
            return {"status": "not_applicable", "message": "QSVM has no trainable circuit parameter vector in the persisted artifact."}
        parameters = np.asarray(artifact["parameters"], dtype=float)
        config = record["configuration"]
        rows = []
        for index in range(min(len(parameters), top_k)):
            plus = parameters.copy(); minus = parameters.copy(); plus[index] += delta; minus[index] -= delta
            if model_type == "vqc":
                plus_value = VQCService.probability(row, plus, config["ansatz_reps"], entanglement); minus_value = VQCService.probability(row, minus, config["ansatz_reps"], entanglement)
            else:
                plus_value = QNNService.raw_prediction(row, plus, config["ansatz_reps"], entanglement); minus_value = QNNService.raw_prediction(row, minus, config["ansatz_reps"], entanglement)
            rows.append({"parameter_index": index, "sensitivity": float((plus_value - minus_value) / 2.0)})
        return {"status": "measured", "parameter_count": len(parameters), "top_parameters": sorted(rows, key=lambda item: -abs(item["sensitivity"]))}
