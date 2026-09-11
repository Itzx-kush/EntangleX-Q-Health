from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from typing import Any

from app.storage.database import sqlite_path


SCHEMA = """
CREATE TABLE IF NOT EXISTS benchmark_reports(
 id TEXT PRIMARY KEY,
 primary_metric TEXT NOT NULL,
 experiment_ids_json TEXT NOT NULL,
 request_json TEXT NOT NULL,
 report_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_benchmark_created ON benchmark_reports(created_at);
"""


class BenchmarkRepository:
    def __init__(self, database_url: str | None = None):
        self.path = sqlite_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def create(self, record: dict[str, Any]) -> None:
        with closing(self.connect()) as connection:
            connection.execute(
                "INSERT INTO benchmark_reports VALUES(?,?,?,?,?,?)",
                (record["id"], record["primary_metric"], json.dumps(record["experiment_ids"]), json.dumps(record["request"]), json.dumps(record["report"]), record["created_at"]),
            )
            connection.commit()

    def get(self, benchmark_id: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM benchmark_reports WHERE id=?", (benchmark_id,)).fetchone()
        if not row:
            return None
        return {"id": row["id"], "primary_metric": row["primary_metric"], "experiment_ids": json.loads(row["experiment_ids_json"]), "request": json.loads(row["request_json"]), "report": json.loads(row["report_json"]), "created_at": row["created_at"]}

    def list(self) -> list[dict[str, Any]]:
        with closing(self.connect()) as connection:
            rows = connection.execute("SELECT * FROM benchmark_reports ORDER BY created_at DESC").fetchall()
        return [{"id": row["id"], "primary_metric": row["primary_metric"], "experiment_ids": json.loads(row["experiment_ids_json"]), "report": json.loads(row["report_json"]), "created_at": row["created_at"]} for row in rows]
