from datetime import datetime, timezone
from time import perf_counter
import uuid
import numpy as np
from scipy.optimize import minimize
from app.core.config import settings
from app.evaluation.metrics import evaluate_binary
from app.quantum.errors import QuantumRuntimeError
from app.quantum.qml_repository import QMLRepository
from app.quantum.model_utils import bounded_subset, circuit_resources, load_encoding_artifact, regression_metrics
from app.quantum.vqc import VQCService


class QNNService:
    def __init__(self, runs=None, artifact_dir=None):
        self.runs = runs or QMLRepository()
        self.artifact_dir = artifact_dir or settings.model_dir / "qnn"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def expectations(features, quantum_parameters, reps, entanglement):
        try:
            from qiskit.quantum_info import Statevector
        except ImportError as exc:
            raise QuantumRuntimeError("QISKIT_UNAVAILABLE", "Install Qiskit before QNN training.") from exc
        circuit = VQCService.circuit(features, quantum_parameters, reps, entanglement)
        state = Statevector.from_instruction(circuit)
        return np.asarray([float(state.probabilities([wire])[0] - state.probabilities([wire])[1]) for wire in range(len(features))])

    @classmethod
    def raw_prediction(cls, features, parameters, reps, entanglement):
        n = len(features)
        quantum_count = n * reps
        quantum_parameters = parameters[:quantum_count]
        head_weights = parameters[quantum_count:quantum_count + n]
        bias = parameters[-1]
        return float(np.dot(head_weights, cls.expectations(features, quantum_parameters, reps, entanglement)) + bias)

    @staticmethod
    def sigmoid(values):
        values = np.clip(values, -30.0, 30.0)
        return 1.0 / (1.0 + np.exp(-values))

    def train(self, config):
        encoding, artifact = load_encoding_artifact(self.runs, config.encoding_run_id)
        artifact_task = encoding.get("summary", {}).get("task_type", "classification")
        if config.task_type != artifact_task:
            raise QuantumRuntimeError("TASK_TYPE_MISMATCH", "QNN task type must match the preprocessing and encoding artifact.", f"Artifact: {artifact_task}; requested: {config.task_type}.")
        X, y = bounded_subset(artifact["train_features"], artifact["train_labels"], config.training_samples, config.seed, config.task_type)
        Xt, yt = bounded_subset(artifact["test_features"], artifact["test_labels"], config.evaluation_samples, config.seed + 1, config.task_type)
        y = np.asarray(y, dtype=float)
        yt = np.asarray(yt, dtype=float)
        if config.task_type == "classification" and len(np.unique(y)) != 2:
            raise QuantumRuntimeError("BINARY_TARGET_REQUIRED", "QNN classification requires exactly two target classes.")
        if config.task_type == "regression":
            if len(np.unique(y)) < 3:
                raise QuantumRuntimeError("CONTINUOUS_TARGET_REQUIRED", "QNN regression requires at least three distinct numeric target values.")
            target_mean = float(np.mean(y))
            target_scale = float(np.std(y)) or 1.0
            objective_y = (y - target_mean) / target_scale
        else:
            target_mean, target_scale, objective_y = 0.0, 1.0, y
        n = X.shape[1]
        parameter_count = n * config.ansatz_reps + n + 1
        rng = np.random.default_rng(config.seed)
        initial = rng.normal(0.0, 0.12, parameter_count)
        history: list[float] = []
        entanglement = encoding["configuration"]["entanglement"]

        def raw(parameters, values):
            return np.asarray([self.raw_prediction(row, parameters, config.ansatz_reps, entanglement) for row in values])

        def objective(parameters):
            predictions = raw(parameters, X)
            if config.task_type == "classification":
                probabilities = np.clip(self.sigmoid(predictions), 1e-7, 1.0 - 1e-7)
                loss = float(-np.mean(objective_y * np.log(probabilities) + (1.0 - objective_y) * np.log(1.0 - probabilities)))
            else:
                loss = float(np.mean((predictions - objective_y) ** 2))
            history.append(loss)
            return loss

        started = perf_counter()
        initial_loss = objective(initial)
        method = "COBYLA" if config.optimizer == "cobyla" else "Nelder-Mead"
        options = {"maxiter": config.max_iterations}
        if method == "COBYLA":
            options.update({"rhobeg": 0.4, "tol": config.tolerance})
        else:
            options.update({"xatol": config.tolerance, "fatol": config.tolerance})
        result = minimize(objective, initial, method=method, options=options)
        duration = round(perf_counter() - started, 6)
        raw_test = raw(result.x, Xt)
        if config.task_type == "classification":
            scores = self.sigmoid(raw_test)
            metrics = evaluate_binary(yt, (scores >= 0.5).astype(int), scores)
        else:
            predictions = raw_test * target_scale + target_mean
            metrics = regression_metrics(yt, predictions)
        metrics.update({"initial_loss": float(initial_loss), "final_loss": float(result.fun), "best_loss": float(min(history))})
        sample = VQCService.circuit(X[0], result.x[: n * config.ansatz_reps], config.ansatz_reps, entanglement)
        run_id = str(uuid.uuid4())
        output = self.artifact_dir / f"{run_id}.npz"
        np.savez_compressed(output, parameters=result.x, loss_history=np.asarray(history), target_mean=target_mean, target_scale=target_scale)
        summary = {
            "training_rows": int(len(X)), "evaluation_rows": int(len(Xt)), "parameter_count": int(parameter_count),
            "training_duration_seconds": duration, **circuit_resources(sample), "metrics": metrics,
            "training_history": [float(value) for value in history], "converged": bool(result.success),
            "optimizer_message": str(result.message),
        }
        record = {
            "id": run_id, "model_type": "qnn", "task_type": config.task_type,
            "encoding_run_id": config.encoding_run_id, "preprocessing_run_id": encoding["preprocessing_run_id"],
            "dataset_id": encoding["dataset_id"], "status": "completed", "configuration": config.model_dump(),
            "summary": summary, "artifact_path": f"qnn/{run_id}.npz", "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.runs.create_model(record)
        return self._response(record)

    def get(self, run_id):
        record = self.runs.get_model(run_id, "qnn")
        if not record:
            raise QuantumRuntimeError("QNN_RUN_NOT_FOUND", "QNN run was not found.", run_id, 404)
        return self._response(record)

    @staticmethod
    def _response(record):
        return {
            "id": record["id"], "model_type": record["model_type"], "task_type": record["task_type"],
            "encoding_run_id": record["encoding_run_id"], "preprocessing_run_id": record["preprocessing_run_id"],
            "dataset_id": record["dataset_id"], "status": record["status"], "configuration": record["configuration"],
            **record["summary"], "artifact_path": record["artifact_path"], "created_at": record["created_at"],
        }
