from datetime import datetime, timezone
from time import perf_counter
from pathlib import Path
import uuid
import joblib
import numpy as np
from sklearn.svm import SVC
from app.core.config import settings
from app.evaluation.metrics import evaluate_binary
from app.quantum.errors import QuantumRuntimeError
from app.quantum.qml_repository import QMLRepository
from app.quantum.model_utils import bounded_subset, circuit_resources, feature_map_circuit, feature_states, fidelity_kernel, load_encoding_artifact


class QSVMService:
    def __init__(self, runs=None, artifact_dir=None):
        self.runs = runs or QMLRepository()
        self.artifact_dir = artifact_dir or settings.model_dir / "qsvm"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def kernel_alignment(kernel, labels):
        signed = np.where(np.asarray(labels) == 1, 1.0, -1.0)
        target = np.outer(signed, signed)
        denominator = np.linalg.norm(kernel) * np.linalg.norm(target)
        return float(np.sum(kernel * target) / denominator) if denominator else 0.0

    def train(self, config):
        encoding, artifact = load_encoding_artifact(self.runs, config.encoding_run_id)
        task_type = encoding.get("summary", {}).get("task_type", "classification")
        if config.task_type != "classification" or task_type != "classification":
            raise QuantumRuntimeError("QSVM_CLASSIFICATION_ONLY", "QSVM currently requires a classification encoding artifact.")
        X, y = bounded_subset(artifact["train_features"], artifact["train_labels"], config.training_samples, config.seed, "classification")
        Xt, yt = bounded_subset(artifact["test_features"], artifact["test_labels"], config.evaluation_samples, config.seed + 1, "classification")
        if len(np.unique(y)) != 2:
            raise QuantumRuntimeError("BINARY_TARGET_REQUIRED", "QSVM requires exactly two training classes.")
        entanglement = encoding["configuration"]["entanglement"]
        started = perf_counter()
        train_states = feature_states(X, entanglement)
        test_states = feature_states(Xt, entanglement)
        train_kernel = fidelity_kernel(train_states, train_states)
        test_kernel = fidelity_kernel(test_states, train_states)
        class_weight = None if config.class_weight == "none" else "balanced"
        model = SVC(kernel="precomputed", C=config.regularization_c, class_weight=class_weight, probability=True, random_state=config.seed)
        model.fit(train_kernel, y)
        predictions = model.predict(test_kernel)
        positive_index = int(np.flatnonzero(model.classes_ == 1)[0])
        scores = model.predict_proba(test_kernel)[:, positive_index]
        duration = round(perf_counter() - started, 6)
        metrics = evaluate_binary(yt, predictions, scores)
        metrics.update({
            "kernel_alignment": self.kernel_alignment(train_kernel, y),
            "support_vectors": int(len(model.support_)),
            "train_kernel_min": float(train_kernel.min()),
            "train_kernel_max": float(train_kernel.max()),
        })
        sample = feature_map_circuit(X[0], entanglement)
        run_id = str(uuid.uuid4())
        output = self.artifact_dir / f"{run_id}.joblib"
        joblib.dump({
            "model": model,
            "training_states": train_states,
            "training_labels": np.asarray(y),
            "configuration": config.model_dump(),
            "encoding_run_id": config.encoding_run_id,
        }, output)
        summary = {
            "training_rows": int(len(X)),
            "evaluation_rows": int(len(Xt)),
            "parameter_count": 0,
            "training_duration_seconds": duration,
            **circuit_resources(sample),
            "metrics": metrics,
            "training_history": [],
            "converged": True,
            "optimizer_message": "Convex SVM optimization completed.",
        }
        record = {
            "id": run_id,
            "model_type": "qsvm",
            "task_type": "classification",
            "encoding_run_id": config.encoding_run_id,
            "preprocessing_run_id": encoding["preprocessing_run_id"],
            "dataset_id": encoding["dataset_id"],
            "status": "completed",
            "configuration": config.model_dump(),
            "summary": summary,
            "artifact_path": f"qsvm/{run_id}.joblib",
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.runs.create_model(record)
        return self._response(record)

    def get(self, run_id):
        record = self.runs.get_model(run_id, "qsvm")
        if not record:
            raise QuantumRuntimeError("QSVM_RUN_NOT_FOUND", "QSVM run was not found.", run_id, 404)
        return self._response(record)

    @staticmethod
    def _response(record):
        return {
            "id": record["id"], "model_type": record["model_type"], "task_type": record["task_type"],
            "encoding_run_id": record["encoding_run_id"], "preprocessing_run_id": record["preprocessing_run_id"],
            "dataset_id": record["dataset_id"], "status": record["status"], "configuration": record["configuration"],
            **record["summary"], "artifact_path": record["artifact_path"], "created_at": record["created_at"],
        }
