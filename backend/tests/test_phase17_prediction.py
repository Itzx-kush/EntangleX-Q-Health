from __future__ import annotations
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from app.ml.repository import ModelRepository
from app.prediction.schemas import PredictionRequest
from app.prediction.service import PredictionService

def test_prediction_uses_real_held_out_sample_and_persists(tmp_path):
    database = f"sqlite:///{tmp_path / 'prediction.db'}"
    features = np.asarray([[0.0, 0.0], [1.0, 1.0], [0.2, 0.1], [0.9, 0.8]])
    labels = np.asarray([0, 1, 0, 1])
    estimator = LogisticRegression(random_state=42).fit(features, labels)
    artifact_path = tmp_path / "model.joblib"
    joblib.dump({"model": estimator, "test_features": features, "feature_names": ["age_scaled", "marker_scaled"], "task_type": "classification"}, artifact_path)
    ModelRepository(database).create({"id":"model-1","preprocessing_run_id":"prep-1","dataset_id":"dataset-1","status":"completed","model_type":"logistic_regression","configuration":{"task_type":"classification"},"summary":{},"artifact_path":str(artifact_path),"created_at":"2026-01-01T00:00:00+00:00"})
    service = PredictionService(database)
    result = service.predict(PredictionRequest(model_run_id="model-1", sample_index=2))
    assert result["input_source"] == "recorded_held_out_sample"
    assert result["feature_count"] == 2
    assert result["probability"] is not None
    assert service.list("model-1")[0]["id"] == result["id"]

def test_prediction_requires_explicit_input(tmp_path):
    service = PredictionService(f"sqlite:///{tmp_path / 'prediction.db'}")
    from app.prediction.errors import PredictionError
    from unittest.mock import patch
    with patch.object(service.models, "get", return_value=None):
        try:
            service.predict(PredictionRequest(model_run_id="missing", sample_index=0))
        except PredictionError as exc:
            assert exc.code == "MODEL_NOT_FOUND"
        else:
            raise AssertionError("missing model should fail honestly")
