from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any

from app.storage.database import sqlite_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS explainability_reports(
 id TEXT PRIMARY KEY,
 phase TEXT NOT NULL,
 target_type TEXT NOT NULL,
 run_id TEXT NOT NULL,
 payload_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_explainability_phase ON explainability_reports(phase, created_at);
CREATE INDEX IF NOT EXISTS idx_explainability_run ON explainability_reports(run_id, created_at);
"""


class ExplainabilityRepository:
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
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO explainability_reports VALUES(?,?,?,?,?,?)",
                (record["id"], record["phase"], record["target_type"], record["run_id"], json.dumps(record["payload"]), record["created_at"]),
            )
            connection.commit()

    def get(self, report_id: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM explainability_reports WHERE id=?", (report_id,)).fetchone()
            return self._decode(row) if row else None

    def list(self, phase: str | None = None) -> list[dict[str, Any]]:
        with closing(self.connect()) as connection:
            if phase:
                rows = connection.execute("SELECT * FROM explainability_reports WHERE phase=? ORDER BY created_at DESC", (phase,)).fetchall()
            else:
                rows = connection.execute("SELECT * FROM explainability_reports ORDER BY created_at DESC").fetchall()
            return [self._decode(row) for row in rows]

    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        value = dict(row)
        value["payload"] = json.loads(value.pop("payload_json"))
        return value
