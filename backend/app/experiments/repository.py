from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any

from app.storage.database import sqlite_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments(
 id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 description TEXT NOT NULL,
 task_type TEXT NOT NULL,
 model_family TEXT NOT NULL,
 modality TEXT NOT NULL,
 status TEXT NOT NULL,
 configuration_json TEXT NOT NULL,
 environment_json TEXT NOT NULL,
 seeds_json TEXT NOT NULL,
 artifacts_json TEXT NOT NULL,
 parent_experiment_id TEXT,
 result_references_json TEXT NOT NULL,
 recorded_results_json TEXT NOT NULL,
 dataset_card_json TEXT,
 model_card_json TEXT,
 scientific_warnings_json TEXT NOT NULL,
 created_at TEXT NOT NULL,
 updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_experiments_created ON experiments(created_at);
CREATE INDEX IF NOT EXISTS idx_experiments_status ON experiments(status);
CREATE INDEX IF NOT EXISTS idx_experiments_model ON experiments(model_family, modality);
"""


class ExperimentRepository:
    def __init__(self, database_url: str | None = None):
        self.path = sqlite_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self) -> None:
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def create(self, record: dict[str, Any]) -> None:
        columns = (
            "id", "name", "description", "task_type", "model_family", "modality", "status",
            "configuration_json", "environment_json", "seeds_json", "artifacts_json",
            "parent_experiment_id", "result_references_json", "recorded_results_json",
            "dataset_card_json", "model_card_json", "scientific_warnings_json", "created_at", "updated_at",
        )
        values = (
            record["id"], record["name"], record["description"], record["task_type"],
            record["model_family"], record["modality"], record["status"],
            json.dumps(record["configuration"]), json.dumps(record["environment"]),
            json.dumps(record["seeds"]), json.dumps(record["artifacts"]),
            record.get("parent_experiment_id"), json.dumps(record["result_references"]),
            json.dumps(record["recorded_results"]),
            json.dumps(record["dataset_card"]) if record.get("dataset_card") is not None else None,
            json.dumps(record["model_card"]) if record.get("model_card") is not None else None,
            json.dumps(record["scientific_warnings"]), record["created_at"], record["updated_at"],
        )
        with closing(self.connect()) as connection:
            placeholders = ",".join("?" for _ in columns)
            connection.execute(
                f"INSERT INTO experiments ({','.join(columns)}) VALUES ({placeholders})", values
            )
            connection.commit()

    def get(self, experiment_id: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM experiments WHERE id=?", (experiment_id,)).fetchone()
            return self._decode(row) if row else None

    def delete(self, experiment_id: str) -> None:
        with closing(self.connect()) as connection:
            connection.execute("DELETE FROM experiments WHERE id=?", (experiment_id,))
            connection.commit()

    def list(
        self,
        search: str | None = None,
        status: str | None = None,
        task_type: str | None = None,
        model_family: str | None = None,
        modality: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        params: list[str] = []
        if search:
            clauses.append("(name LIKE ? OR description LIKE ? OR model_family LIKE ?)")
            pattern = f"%{search}%"
            params.extend([pattern, pattern, pattern])
        for field, value in (("status", status), ("task_type", task_type), ("model_family", model_family), ("modality", modality)):
            if value:
                clauses.append(f"{field}=?")
                params.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with closing(self.connect()) as connection:
            rows = connection.execute(
                f"SELECT * FROM experiments{where} ORDER BY created_at DESC", params
            ).fetchall()
            return [self._decode(row) for row in rows]

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        mappings = {
            "configuration_json": "configuration",
            "environment_json": "environment",
            "seeds_json": "seeds",
            "artifacts_json": "artifacts",
            "result_references_json": "result_references",
            "recorded_results_json": "recorded_results",
            "dataset_card_json": "dataset_card",
            "model_card_json": "model_card",
            "scientific_warnings_json": "scientific_warnings",
        }
        for source, target in mappings.items():
            raw = value.pop(source)
            value[target] = json.loads(raw) if raw is not None else None
        return value
