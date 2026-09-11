from __future__ import annotations
from dataclasses import dataclass
import os
from pathlib import Path


def _bool(name: str, default: bool = False) -> bool:
    return os.getenv(name, str(default)).lower() in {"1", "true", "yes", "on"}

@dataclass(frozen=True)
class Settings:
    app_name: str = "EntangleX Q-Health"
    app_env: str = os.getenv("APP_ENV", "development")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./entanglex.db")
    cors_origins: tuple[str, ...] = tuple(x.strip() for x in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if x.strip())
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "./data/uploads"))
    model_dir: Path = Path(os.getenv("MODEL_DIR", "./models"))
    experiment_dir: Path = Path(os.getenv("EXPERIMENT_DIR", "./experiments"))
    max_upload_size_mb: int = int(os.getenv("MAX_UPLOAD_SIZE_MB", "25"))
    default_seed: int = int(os.getenv("DEFAULT_RANDOM_SEED", "42"))
    default_qubits: int = int(os.getenv("DEFAULT_QUBITS", "4"))
    max_qubits: int = int(os.getenv("MAX_QUBITS", "8"))
    quantum_backend: str = os.getenv("QUANTUM_BACKEND", "aer_simulator")
    max_quantum_shots: int = int(os.getenv("MAX_QUANTUM_SHOTS", "8192"))
    enable_real_quantum: bool = _bool("ENABLE_REAL_QUANTUM")

    def validate(self) -> None:
        if not 1 <= self.default_qubits <= self.max_qubits <= 8:
            raise ValueError("Qubit settings must satisfy 1 <= default <= max <= 8 for the MVP.")
        if not 1 <= self.max_quantum_shots <= 8192:
            raise ValueError("MAX_QUANTUM_SHOTS must be between 1 and 8192.")
        if self.max_upload_size_mb <= 0:
            raise ValueError("MAX_UPLOAD_SIZE_MB must be positive.")

settings = Settings()
settings.validate()
