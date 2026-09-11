from __future__ import annotations
import hashlib
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
import joblib
import numpy as np
from app.ml.repository import ModelRepository
from app.prediction.errors import PredictionError
from app.prediction.repository import PredictionRepository
from app.prediction.schemas import PredictionRequest

class PredictionService:
    def __init__(self, database_url: str | None = None):
        self.models = ModelRepository(database_url)
        self.records = PredictionRepository(database_url)

    def predict(self, request: PredictionRequest):
        model_record = self.models.get(request.model_run_id)
        if not model_record:
            raise PredictionError("MODEL_NOT_FOUND", "The selected model run was not found.", 404)
        artifact_path = Path(model_record["artifact_path"])
        if not artifact_path.exists():
            raise PredictionError("ARTIFACT_NOT_FOUND", "The model artifact is unavailable; no prediction was generated.", 409, {"artifact_path": str(artifact_path)})
        try:
            artifact = joblib.load(artifact_path)
            estimator = artifact["model"]
            test_features = np.asarray(artifact["test_features"], dtype=float)
            feature_names = list(artifact.get("feature_names", []))
        except Exception as exc:
            raise PredictionError("ARTIFACT_LOAD_FAILED", "The persisted model artifact could not be loaded.", 422, {"reason": str(exc)}) from exc
        if request.features is not None and request.sample_index is not None:
            raise PredictionError("MULTIPLE_INPUT_SOURCES", "Provide features or sample_index, not both.")
        if request.features is None and request.sample_index is None:
            raise PredictionError("INPUT_REQUIRED", "Choose a recorded held-out sample or provide a feature vector. No input was fabricated.")
        if request.features is not None:
            vector = np.asarray(request.features, dtype=float)
            source = "provided_feature_vector"
            sample_index = None
        else:
            if request.sample_index >= len(test_features):
                raise PredictionError("SAMPLE_INDEX_OUT_OF_RANGE", "The held-out sample index is outside the persisted test partition.", 422, {"available_samples": len(test_features)})
            vector = test_features[request.sample_index]
            source = "recorded_held_out_sample"
            sample_index = request.sample_index
        if vector.ndim != 1 or vector.size != test_features.shape[1]:
            raise PredictionError("FEATURE_COUNT_MISMATCH", "The input feature count does not match the persisted model artifact.", 422, {"expected": int(test_features.shape[1]), "received": int(vector.size)})
        if not np.isfinite(vector).all():
            raise PredictionError("NON_FINITE_FEATURES", "All prediction features must be finite numbers.")
        X = vector.reshape(1, -1)
        try:
            raw_prediction = estimator.predict(X)[0]
        except Exception as exc:
            raise PredictionError("PREDICTION_FAILED", "The persisted model rejected this input.", 422, {"reason": str(exc)}) from exc
        task_type = model_record["configuration"].get("task_type", artifact.get("task_type", "classification"))
        probability = self._probability(estimator, X, raw_prediction, task_type)
        if task_type == "classification":
            prediction_value = int(raw_prediction) if isinstance(raw_prediction, (int, np.integer)) else str(raw_prediction)
            risk_band = self._risk_band(probability, request)
            threshold = request.probability_threshold if probability is not None else None
            decision = "positive" if probability is not None and probability >= request.probability_threshold else ("not_available" if probability is None else "negative")
            uncertainty = "descriptive_single_prediction"
            boundaries = {"low_max": request.low_risk_max, "intermediate_max": request.intermediate_risk_max} if probability is not None else None
        else:
            prediction_value = float(raw_prediction)
            risk_band = "not_applicable"
            threshold = None
            decision = "regression_estimate"
            uncertainty = "not_calculated_from_single_prediction"
            boundaries = None
        now = datetime.now(timezone.utc).isoformat()
        record = {"id": str(uuid.uuid4()), "model_run_id": request.model_run_id, "model_type": model_record["model_type"], "task_type": task_type, "input_source": source, "sample_index": sample_index, "feature_count": int(vector.size), "input_sha256": hashlib.sha256(vector.tobytes()).hexdigest(), "prediction": {"value": prediction_value, "probability": probability, "threshold": threshold, "risk_band": risk_band, "risk_band_boundaries": boundaries, "decision": decision, "uncertainty_status": uncertainty, "feature_names": feature_names}, "created_at": now}
        self.records.create(record)
        return {"id": record["id"], "model_run_id": record["model_run_id"], "model_type": record["model_type"], "task_type": record["task_type"], "input_source": source, "sample_index": sample_index, "feature_count": record["feature_count"], **record["prediction"], "scientific_warnings": ["Research decision support only; this is not a clinical diagnosis.", "Risk bands are configurable descriptive thresholds, not validated clinical categories.", "Single-record uncertainty is not inferred from this prediction."], "created_at": now}

    def get(self, record_id: str):
        item = self.records.get(record_id)
        if not item:
            raise PredictionError("PREDICTION_NOT_FOUND", "The prediction record was not found.", 404)
        return self._response(item)
    def list(self, model_run_id: str | None = None):
        return [self._response(item) for item in self.records.list(model_run_id)]
    @staticmethod
    def _probability(estimator, X, raw_prediction, task_type):
        if task_type != "classification":
            return None
        if hasattr(estimator, "predict_proba"):
            try:
                probabilities = np.asarray(estimator.predict_proba(X), dtype=float)
                if probabilities.ndim == 2 and probabilities.shape[1] >= 2:
                    classes = list(getattr(estimator, "classes_", range(probabilities.shape[1])))
                    positive = classes.index(1) if 1 in classes else probabilities.shape[1] - 1
                    return float(probabilities[0, positive])
            except Exception:
                return None
        return None
    @staticmethod
    def _risk_band(probability, request):
        if probability is None:
            return "not_available"
        if probability < request.low_risk_max:
            return "low"
        if probability < request.intermediate_risk_max:
            return "intermediate"
        return "high"
    @staticmethod
    def _response(item):
        prediction = item["prediction"]
        return {"id": item["id"], "model_run_id": item["model_run_id"], "model_type": item["model_type"], "task_type": item["task_type"], "input_source": item["input_source"], "sample_index": item["sample_index"], "feature_count": item["feature_count"], **prediction, "scientific_warnings": ["Research decision support only; this is not a clinical diagnosis.", "Risk bands are configurable descriptive thresholds, not validated clinical categories.", "Single-record uncertainty is not inferred from this prediction."], "created_at": item["created_at"]}
