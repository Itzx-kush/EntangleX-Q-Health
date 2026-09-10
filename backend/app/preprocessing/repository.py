from __future__ import annotations
import json, sqlite3
from contextlib import closing
from typing import Any
from app.storage.database import sqlite_path
SCHEMA="""CREATE TABLE IF NOT EXISTS preprocessing_runs(id TEXT PRIMARY KEY,dataset_id TEXT NOT NULL,status TEXT NOT NULL,configuration_json TEXT NOT NULL,summary_json TEXT NOT NULL,artifact_path TEXT NOT NULL,created_at TEXT NOT NULL);CREATE INDEX IF NOT EXISTS idx_preprocessing_dataset ON preprocessing_runs(dataset_id,created_at);"""
class PreprocessingRepository:
    def __init__(self,database_url:str|None=None)->None:self.path=sqlite_path(database_url);self.path.parent.mkdir(parents=True,exist_ok=True);self.ensure_schema()
    def connect(self):
        connection=sqlite3.connect(self.path);connection.row_factory=sqlite3.Row;return connection
    def ensure_schema(self):
        with closing(self.connect()) as connection:connection.executescript(SCHEMA);connection.commit()
    def create(self,record:dict[str,Any]):
        with closing(self.connect()) as connection:connection.execute("INSERT INTO preprocessing_runs VALUES(?,?,?,?,?,?,?)",(record["id"],record["dataset_id"],record["status"],json.dumps(record["configuration"]),json.dumps(record["summary"]),record["artifact_path"],record["created_at"]));connection.commit()
    def get(self,run_id:str):
        with closing(self.connect()) as connection:row=connection.execute("SELECT * FROM preprocessing_runs WHERE id=?",(run_id,)).fetchone();return self._decode(row) if row else None
    def list(self,dataset_id:str|None=None):
        with closing(self.connect()) as connection:
            rows=connection.execute("SELECT * FROM preprocessing_runs WHERE dataset_id=? ORDER BY created_at DESC",(dataset_id,)).fetchall() if dataset_id else connection.execute("SELECT * FROM preprocessing_runs ORDER BY created_at DESC").fetchall();return [self._decode(row) for row in rows]
    @staticmethod
    def _decode(row):
        value=dict(row);value["configuration"]=json.loads(value.pop("configuration_json"));value["summary"]=json.loads(value.pop("summary_json"));return value
