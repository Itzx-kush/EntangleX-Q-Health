from __future__ import annotations
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any
from app.storage.database import sqlite_path

SCHEMA="""
CREATE TABLE IF NOT EXISTS datasets (
 id TEXT PRIMARY KEY,
 name TEXT NOT NULL,
 original_filename TEXT NOT NULL,
 stored_filename TEXT NOT NULL,
 content_type TEXT,
 extension TEXT NOT NULL,
 size_bytes INTEGER NOT NULL,
 sha256 TEXT NOT NULL,
 profile_json TEXT NOT NULL,
 target_column TEXT,
 target_json TEXT,
 warnings_json TEXT NOT NULL,
 created_at TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_datasets_sha256 ON datasets(sha256);
"""

class DatasetRepository:
    def __init__(self, database_url: str | None=None) -> None:
        self.path=sqlite_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()
    def connect(self):
        connection=sqlite3.connect(self.path)
        connection.row_factory=sqlite3.Row
        return connection
    def ensure_schema(self) -> None:
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA); connection.commit()
    def create(self, record: dict[str, Any]) -> None:
        with closing(self.connect()) as connection:
            connection.execute("INSERT INTO datasets (id,name,original_filename,stored_filename,content_type,extension,size_bytes,sha256,profile_json,target_column,target_json,warnings_json,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",(record["id"],record["name"],record["original_filename"],record["stored_filename"],record.get("content_type"),record["extension"],record["size_bytes"],record["sha256"],json.dumps(record["profile"]),record.get("target_column"),json.dumps(record.get("target")) if record.get("target") else None,json.dumps(record.get("warnings",[])),record["created_at"])); connection.commit()
    def find_by_hash(self, digest: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row=connection.execute("SELECT * FROM datasets WHERE sha256=?",(digest,)).fetchone()
            return self._decode(row) if row else None
    def get(self, dataset_id: str) -> dict[str, Any] | None:
        with closing(self.connect()) as connection:
            row=connection.execute("SELECT * FROM datasets WHERE id=?",(dataset_id,)).fetchone()
            return self._decode(row) if row else None
    def list(self) -> list[dict[str, Any]]:
        with closing(self.connect()) as connection:
            rows=connection.execute("SELECT * FROM datasets ORDER BY created_at DESC").fetchall()
            return [self._decode(row) for row in rows]
    def update_target(self, dataset_id: str, target_column: str, target: dict[str, Any], warnings: list[str]) -> None:
        with closing(self.connect()) as connection:
            connection.execute("UPDATE datasets SET target_column=?, target_json=?, warnings_json=? WHERE id=?",(target_column,json.dumps(target),json.dumps(warnings),dataset_id)); connection.commit()
    @staticmethod
    def _decode(row: sqlite3.Row) -> dict[str, Any]:
        value=dict(row); value["profile"]=json.loads(value.pop("profile_json")); value["target"]=json.loads(value.pop("target_json")) if value.get("target_json") else None; value.pop("target_json",None); value["warnings"]=json.loads(value.pop("warnings_json")); return value
