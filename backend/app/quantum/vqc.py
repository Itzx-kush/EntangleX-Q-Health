from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
import uuid
import numpy as np
from scipy.optimize import minimize
from app.core.config import settings
from app.evaluation.metrics import evaluate_binary
from app.quantum.errors import QuantumRuntimeError
from app.quantum.qml_repository import QMLRepository
from app.quantum.encoding import QuantumEncodingService
from app.quantum.model_utils import bounded_subset


class VQCService:
    def __init__(self, runs=None, artifact_dir=None):
        self.runs = runs or QMLRepository()
        self.artifact_dir = artifact_dir or settings.model_dir / "vqc"
        self.artifact_dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def circuit(features, parameters, reps, entanglement):
        circuit = QuantumEncodingService.circuit(features, entanglement)
        n = len(features)
        position = 0
        for _ in range(reps):
            for wire in range(n):
                circuit.ry(float(parameters[position]), wire)
                position += 1
            if n > 1:
                for wire in range(n - 1):
                    circuit.cx(wire, wire + 1)
                if entanglement == "ring" and n > 2:
                    circuit.cx(n - 1, 0)
        return circuit

    @classmethod
    def probability(cls, features, parameters, reps, entanglement):
        from qiskit.quantum_info import Statevector
        probabilities = Statevector.from_instruction(cls.circuit(features, parameters, reps, entanglement)).probabilities([0])
        return float(probabilities[1])

    def train(self, config):
        encoding = self.runs.get_encoding(config.encoding_run_id)
        if not encoding:
            raise QuantumRuntimeError("ENCODING_RUN_NOT_FOUND", "Create a quantum encoding run first.", config.encoding_run_id, 404)
        if encoding.get("summary", {}).get("task_type", "classification") != "classification":
            raise QuantumRuntimeError("VQC_CLASSIFICATION_ONLY", "VQC requires a classification encoding artifact. Use QNN for regression.")
        path = settings.model_dir / "quantum_encoding" / Path(encoding["artifact_path"]).name
        if not path.exists():
            raise QuantumRuntimeError("ENCODING_ARTIFACT_NOT_FOUND", "The encoded feature artifact is missing.", str(path), 404)
        try:
            from qiskit.quantum_info import Statevector  # noqa: F401
        except ImportError as exc:
            raise QuantumRuntimeError("QISKIT_UNAVAILABLE", "Install Qiskit before VQC training.") from exc
        artifact = np.load(path)
        X, y = bounded_subset(artifact["train_features"], artifact["train_labels"], config.training_samples, config.seed, "classification")
        Xt, yt = bounded_subset(artifact["test_features"], artifact["test_labels"], config.evaluation_samples, config.seed + 1, "classification")
        n = X.shape[1]
        rng = np.random.default_rng(config.seed)
        initial = rng.normal(0.0, 0.15, n * config.ansatz_reps)
        history: list[float] = []
        entanglement = encoding["configuration"]["entanglement"]

        def objective(parameters):
            scores = np.clip(np.asarray([self.probability(row, parameters, config.ansatz_reps, entanglement) for row in X]), 1e-7, 1.0 - 1e-7)
            loss = float(-np.mean(y * np.log(scores) + (1.0 - y) * np.log(1.0 - scores)))
            history.append(loss)
            return loss

        started = perf_counter()
        initial_loss = objective(initial)
        method = "COBYLA" if config.optimizer == "cobyla" else "Nelder-Mead"
        options = {"maxiter": config.max_iterations}
        if method == "COBYLA":
            options.update({"rhobeg": 0.5, "tol": config.tolerance})
        else:
            options.update({"xatol": config.tolerance, "fatol": config.tolerance})
        result = minimize(objective, initial, method=method, options=options)
        duration = round(perf_counter() - started, 6)
        scores = np.asarray([self.probability(row, result.x, config.ansatz_reps, entanglement) for row in Xt])
        metrics = evaluate_binary(yt, (scores >= 0.5).astype(int), scores)
        sample = self.circuit(X[0], result.x, config.ansatz_reps, entanglement)
        run_id = str(uuid.uuid4())
        output = self.artifact_dir / f"{run_id}.npz"
        np.savez_compressed(output, parameters=result.x, loss_history=np.asarray(history), configuration=np.asarray([str(config.model_dump())]))
        message = str(result.message)
        summary = {
            "training_rows": len(X), "evaluation_rows": len(Xt), "parameter_count": len(result.x),
            "iterations_completed": int(getattr(result, "nfev", len(history))), "initial_loss": float(initial_loss),
            "final_loss": float(result.fun), "best_loss": float(min(history)), "converged": bool(result.success),
            "termination_reason": "optimizer_converged" if result.success else "optimizer_stopped_without_convergence",
            "optimizer_message": message, "training_duration_seconds": duration, **metrics,
            "circuit_depth": int(sample.depth()), "circuit_size": int(sample.size()),
            "operation_counts": {str(key): int(value) for key, value in sample.count_ops().items()},
            "loss_history": [float(value) for value in history],
        }
        record = {
            "id": run_id, "encoding_run_id": config.encoding_run_id, "preprocessing_run_id": encoding["preprocessing_run_id"],
            "dataset_id": encoding["dataset_id"], "status": "completed", "configuration": config.model_dump(),
            "summary": summary, "artifact_path": f"vqc/{run_id}.npz", "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.runs.create_vqc(record)
        return self._response(record)

    def get(self, run_id):
        record = self.runs.get_vqc(run_id)
        if not record:
            raise QuantumRuntimeError("VQC_RUN_NOT_FOUND", "VQC run was not found.", run_id, 404)
        return self._response(record)

    @staticmethod
    def _response(record):
        summary = dict(record["summary"])
        summary.setdefault("best_loss", summary.get("final_loss", 0.0))
        summary.setdefault("termination_reason", "legacy_run")
        summary.setdefault("optimizer_message", "Legacy Phase 10 run")
        return {
            "id": record["id"], "encoding_run_id": record["encoding_run_id"],
            "preprocessing_run_id": record["preprocessing_run_id"], "dataset_id": record["dataset_id"],
            "status": record["status"], "configuration": record["configuration"], **summary,
            "artifact_path": record["artifact_path"], "created_at": record["created_at"],
        }
