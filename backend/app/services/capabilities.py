from __future__ import annotations
import importlib
import importlib.metadata
import platform
from typing import Any

PACKAGES = {"qiskit": "qiskit", "qiskit_machine_learning": "qiskit-machine-learning", "qiskit_aer": "qiskit-aer", "scikit_learn": "scikit-learn"}

def _probe(module_name: str, distribution: str) -> dict[str, Any]:
    try:
        importlib.import_module(module_name)
        return {"available": True, "version": importlib.metadata.version(distribution)}
    except Exception as exc:
        return {"available": False, "version": None, "reason": f"{type(exc).__name__}: {exc}"}

def runtime_capabilities() -> dict[str, Any]:
    packages = {key: _probe(module, distribution) for key, (module, distribution) in {"qiskit": ("qiskit", "qiskit"), "qiskit_machine_learning": ("qiskit_machine_learning", "qiskit-machine-learning"), "qiskit_aer": ("qiskit_aer", "qiskit-aer"), "scikit_learn": ("sklearn", "scikit-learn")}.items()}
    return {"python": platform.python_version(), "platform": platform.platform(), "packages": packages, "quantum_simulator": "available" if packages["qiskit_aer"]["available"] else "unavailable"}
