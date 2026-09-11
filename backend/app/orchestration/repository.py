from __future__ import annotations
import json
import sqlite3
from contextlib import closing
from typing import Any
from app.storage.database import sqlite_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS training_jobs(
 id TEXT PRIMARY KEY, model_type TEXT NOT NULL, modality TEXT NOT NULL,
 dataset_id TEXT, preprocessing_run_id TEXT, encoding_run_id TEXT,
 status TEXT NOT NULL, progress INTEGER NOT NULL, configuration_json TEXT NOT NULL,
 result_json TEXT, error_json TEXT, cancel_requested INTEGER NOT NULL DEFAULT 0,
 parent_job_id TEXT, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_training_jobs_created ON training_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_training_jobs_dataset ON training_jobs(dataset_id,created_at);
"""

class TrainingJobRepository:
    def __init__(self, database_url: str | None = None):
        self.path = sqlite_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()
    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection
    def ensure_schema(self):
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA); connection.commit()
    def create(self, record: dict[str, Any]):
        with closing(self.connect()) as connection:
            connection.execute("INSERT INTO training_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                record["id"], record["model_type"], record["modality"], record.get("dataset_id"),
                record.get("preprocessing_run_id"), record.get("encoding_run_id"), record["status"], record["progress"],
                json.dumps(record["configuration"]), json.dumps(record.get("result")) if record.get("result") is not None else None,
                json.dumps(record.get("error")) if record.get("error") is not None else None,
                int(record.get("cancel_requested", False)), record.get("parent_job_id"), record["created_at"],
                record.get("started_at"), record.get("finished_at")))
            connection.commit()
    def get(self, job_id: str):
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM training_jobs WHERE id=?", (job_id,)).fetchone()
            return self._decode(row) if row else None
    def list(self, dataset_id: str | None = None):
        with closing(self.connect()) as connection:
            if dataset_id:
                rows = connection.execute("SELECT * FROM training_jobs WHERE dataset_id=? ORDER BY created_at DESC", (dataset_id,)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM training_jobs ORDER BY created_at DESC").fetchall()
            return [self._decode(row) for row in rows]
    def update(self, job_id: str, **fields):
        if not fields: return
        encoded = {}
        for key, value in fields.items():
            if key in {"configuration", "result", "error"}:
                value = json.dumps(value) if value is not None else None
            elif key == "cancel_requested": value = int(value)
            encoded[key] = value
        assignments = ",".join(f"{key}=?" for key in encoded)
        with closing(self.connect()) as connection:
            connection.execute(f"UPDATE training_jobs SET {assignments} WHERE id=?", [*encoded.values(), job_id]); connection.commit()
    @staticmethod
    def _decode(row):
        value = dict(row)
        value["configuration"] = json.loads(value["configuration_json"]); value.pop("configuration_json")
        value["result"] = json.loads(value["result_json"]) if value["result_json"] else None; value.pop("result_json")
        value["error"] = json.loads(value["error_json"]) if value["error_json"] else None; value.pop("error_json")
        value["cancel_requested"] = bool(value["cancel_requested"]); return value
