from pathlib import Path
import numpy as np
from app.core.config import settings
from app.quantum.errors import QuantumRuntimeError


def load_encoding_artifact(runs, encoding_run_id: str):
    encoding = runs.get_encoding(encoding_run_id)
    if not encoding:
        raise QuantumRuntimeError("ENCODING_RUN_NOT_FOUND", "Create a quantum encoding run first.", encoding_run_id, 404)
    path = settings.model_dir / "quantum_encoding" / Path(encoding["artifact_path"]).name
    if not path.exists():
        raise QuantumRuntimeError("ENCODING_ARTIFACT_NOT_FOUND", "The encoded feature artifact is missing.", str(path), 404)
    return encoding, np.load(path)


def bounded_subset(X, y, limit: int, seed: int, task_type: str):
    X = np.asarray(X, dtype=float)
    y = np.asarray(y)
    if len(X) != len(y) or not len(X):
        raise QuantumRuntimeError("INVALID_TRAINING_ARTIFACT", "Encoded features and targets are inconsistent.")
    if len(X) <= limit:
        return X, y
    rng = np.random.default_rng(seed)
    if task_type == "regression":
        chosen = np.sort(rng.choice(len(X), limit, replace=False))
        return X[chosen], y[chosen]
    classes = np.unique(y)
    if len(classes) != 2:
        raise QuantumRuntimeError("BINARY_TARGET_REQUIRED", "Quantum classification requires exactly two target classes.")
    chosen: list[int] = []
    initial_per_class = max(1, limit // len(classes))
    for value in classes:
        indices = np.flatnonzero(y == value)
        take = min(len(indices), initial_per_class)
        chosen.extend(rng.choice(indices, take, replace=False).tolist())
    remaining = limit - len(chosen)
    if remaining > 0:
        available = np.setdiff1d(np.arange(len(y)), np.asarray(chosen), assume_unique=False)
        chosen.extend(rng.choice(available, min(remaining, len(available)), replace=False).tolist())
    selected = np.asarray(chosen[:limit], dtype=int)
    rng.shuffle(selected)
    if len(np.unique(y[selected])) != 2:
        raise QuantumRuntimeError("BINARY_SUBSET_FAILED", "The bounded sample did not preserve both target classes.")
    return X[selected], y[selected]


def regression_metrics(y_true, predictions):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    y_true = np.asarray(y_true, dtype=float)
    predictions = np.asarray(predictions, dtype=float)
    mse = float(mean_squared_error(y_true, predictions))
    return {
        "mae": float(mean_absolute_error(y_true, predictions)),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": float(r2_score(y_true, predictions)) if len(y_true) > 1 else None,
        "target_mean": float(np.mean(y_true)),
        "prediction_mean": float(np.mean(predictions)),
        "prediction_min": float(np.min(predictions)),
        "prediction_max": float(np.max(predictions)),
    }


def feature_map_circuit(values, entanglement: str):
    from qiskit import QuantumCircuit
    values = np.asarray(values, dtype=float)
    n = len(values)
    circuit = QuantumCircuit(n, name="entanglex_quantum_kernel_map")
    for wire, value in enumerate(values):
        circuit.h(wire)
        circuit.rz(2.0 * float(value), wire)
        circuit.ry(float(value), wire)
    if n > 1:
        edges = [(wire, wire + 1) for wire in range(n - 1)]
        if entanglement == "ring" and n > 2:
            edges.append((n - 1, 0))
        for left, right in edges:
            circuit.cx(left, right)
            interaction = 2.0 * (np.pi - values[left]) * (np.pi - values[right])
            circuit.rz(float(interaction), right)
            circuit.cx(left, right)
    return circuit


def feature_states(X, entanglement: str):
    try:
        from qiskit.quantum_info import Statevector
    except ImportError as exc:
        raise QuantumRuntimeError("QISKIT_UNAVAILABLE", "Install Qiskit before quantum model training.") from exc
    return np.asarray([
        np.asarray(Statevector.from_instruction(feature_map_circuit(row, entanglement)).data, dtype=complex)
        for row in np.asarray(X, dtype=float)
    ])


def fidelity_kernel(left_states, right_states):
    overlaps = np.asarray(left_states) @ np.asarray(right_states).conjugate().T
    return np.clip(np.abs(overlaps) ** 2, 0.0, 1.0).real


def circuit_resources(circuit):
    return {
        "circuit_depth": int(circuit.depth()),
        "circuit_size": int(circuit.size()),
        "operation_counts": {str(key): int(value) for key, value in circuit.count_ops().items()},
    }
