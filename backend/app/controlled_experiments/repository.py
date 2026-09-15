from __future__ import annotations
import json, sqlite3
from contextlib import closing
from typing import Any
from app.storage.database import sqlite_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS controlled_experiments(
 id TEXT PRIMARY KEY, name TEXT NOT NULL, preprocessing_run_id TEXT NOT NULL,
 encoding_run_id TEXT, comparison_fingerprint TEXT NOT NULL, status TEXT NOT NULL,
 configuration_json TEXT NOT NULL, warnings_json TEXT NOT NULL,
 parent_experiment_id TEXT, created_at TEXT NOT NULL, started_at TEXT, finished_at TEXT
);
CREATE TABLE IF NOT EXISTS controlled_model_jobs(
 id TEXT PRIMARY KEY, experiment_id TEXT NOT NULL, model_type TEXT NOT NULL,
 status TEXT NOT NULL, stage TEXT NOT NULL, checkpoint INTEGER NOT NULL,
 total_checkpoints INTEGER NOT NULL, cancel_requested INTEGER NOT NULL DEFAULT 0,
 result_json TEXT, error_json TEXT, created_at TEXT NOT NULL,
 started_at TEXT, finished_at TEXT,
 FOREIGN KEY(experiment_id) REFERENCES controlled_experiments(id)
);
CREATE INDEX IF NOT EXISTS idx_controlled_jobs_experiment ON controlled_model_jobs(experiment_id);
CREATE INDEX IF NOT EXISTS idx_controlled_experiments_created ON controlled_experiments(created_at);
"""

class ControlledExperimentRepository:
    def __init__(self, database_url: str | None = None):
        self.path = sqlite_path(database_url); self.path.parent.mkdir(parents=True, exist_ok=True); self.ensure_schema()
    def connect(self):
        connection = sqlite3.connect(self.path, timeout=30); connection.row_factory = sqlite3.Row; return connection
    def ensure_schema(self):
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA)
            connection.execute("UPDATE controlled_model_jobs SET status='interrupted',stage='interrupted',finished_at=COALESCE(finished_at,created_at) WHERE status IN ('running','cancel_requested')")
            connection.execute("UPDATE controlled_experiments SET status='interrupted' WHERE status='running'")
            connection.commit()
    def create_experiment(self, value: dict[str, Any]):
        with closing(self.connect()) as c:
            c.execute("INSERT INTO controlled_experiments VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", (value["id"],value["name"],value["preprocessing_run_id"],value.get("encoding_run_id"),value["comparison_fingerprint"],value["status"],json.dumps(value["configuration"]),json.dumps(value["warnings"]),value.get("parent_experiment_id"),value["created_at"],value.get("started_at"),value.get("finished_at"))); c.commit()
    def create_job(self, value: dict[str, Any]):
        with closing(self.connect()) as c:
            c.execute("INSERT INTO controlled_model_jobs VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (value["id"],value["experiment_id"],value["model_type"],value["status"],value["stage"],value["checkpoint"],value["total_checkpoints"],int(value.get("cancel_requested",False)),None,None,value["created_at"],None,None)); c.commit()
    def update_experiment(self, experiment_id: str, **values):
        self._update("controlled_experiments", experiment_id, values)
    def update_job(self, job_id: str, **values):
        encoded = {k:(json.dumps(v) if k in {"result_json","error_json"} and v is not None else int(v) if k=="cancel_requested" else v) for k,v in values.items()}; self._update("controlled_model_jobs",job_id,encoded)
    def _update(self, table: str, identifier: str, values: dict[str, Any]):
        if not values:return
        with closing(self.connect()) as c:
            c.execute(f"UPDATE {table} SET "+",".join(f"{key}=?" for key in values)+" WHERE id=?",(*values.values(),identifier)); c.commit()
    def get_experiment(self, experiment_id: str):
        with closing(self.connect()) as c:
            row=c.execute("SELECT * FROM controlled_experiments WHERE id=?",(experiment_id,)).fetchone(); return self._experiment(row) if row else None
    def list_experiments(self):
        with closing(self.connect()) as c:return [self._experiment(row) for row in c.execute("SELECT * FROM controlled_experiments ORDER BY created_at DESC").fetchall()]
    def get_job(self, job_id: str):
        with closing(self.connect()) as c:
            row=c.execute("SELECT * FROM controlled_model_jobs WHERE id=?",(job_id,)).fetchone(); return self._job(row) if row else None
    def jobs(self, experiment_id: str):
        with closing(self.connect()) as c:return [self._job(row) for row in c.execute("SELECT * FROM controlled_model_jobs WHERE experiment_id=? ORDER BY created_at",(experiment_id,)).fetchall()]
    @staticmethod
    def _experiment(row):
        value=dict(row); value["configuration"]=json.loads(value.pop("configuration_json")); value["warnings"]=json.loads(value.pop("warnings_json")); return value
    @staticmethod
    def _job(row):
        value=dict(row); value["cancel_requested"]=bool(value["cancel_requested"]); value["result"]=json.loads(value.pop("result_json")) if value["result_json"] else None; value["error"]=json.loads(value.pop("error_json")) if value["error_json"] else None; return value
