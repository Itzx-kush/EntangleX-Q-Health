from __future__ import annotations
import json
import sqlite3
from contextlib import closing
from app.storage.database import sqlite_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS prediction_records(
 id TEXT PRIMARY KEY,
 model_run_id TEXT NOT NULL,
 model_type TEXT NOT NULL,
 task_type TEXT NOT NULL,
 input_source TEXT NOT NULL,
 sample_index INTEGER,
 feature_count INTEGER NOT NULL,
 input_sha256 TEXT NOT NULL,
 prediction_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_predictions_model ON prediction_records(model_run_id,created_at);
"""

class PredictionRepository:
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
            connection.executescript(SCHEMA)
            connection.commit()
    def create(self, record: dict):
        with closing(self.connect()) as connection:
            connection.execute("INSERT INTO prediction_records VALUES(?,?,?,?,?,?,?,?,?,?)", (
                record["id"], record["model_run_id"], record["model_type"], record["task_type"],
                record["input_source"], record.get("sample_index"), record["feature_count"],
                record["input_sha256"], json.dumps(record["prediction"]), record["created_at"],
            ))
            connection.commit()
    def get(self, record_id: str):
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM prediction_records WHERE id=?", (record_id,)).fetchone()
            return self._decode(row) if row else None
    def list(self, model_run_id: str | None = None):
        with closing(self.connect()) as connection:
            if model_run_id:
                rows = connection.execute("SELECT * FROM prediction_records WHERE model_run_id=? ORDER BY created_at DESC", (model_run_id,)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM prediction_records ORDER BY created_at DESC").fetchall()
            return [self._decode(row) for row in rows]
    @staticmethod
    def _decode(row):
        value = dict(row)
        value["prediction"] = json.loads(value.pop("prediction_json"))
        value.pop("input_sha256", None)
        return value
