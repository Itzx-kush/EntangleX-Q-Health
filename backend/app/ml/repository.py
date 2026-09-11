import json,sqlite3
from contextlib import closing
from app.storage.database import sqlite_path
SCHEMA="""CREATE TABLE IF NOT EXISTS model_runs(id TEXT PRIMARY KEY,preprocessing_run_id TEXT NOT NULL,dataset_id TEXT NOT NULL,status TEXT NOT NULL,model_type TEXT NOT NULL,configuration_json TEXT NOT NULL,summary_json TEXT NOT NULL,artifact_path TEXT NOT NULL,created_at TEXT NOT NULL);CREATE INDEX IF NOT EXISTS idx_model_preprocessing ON model_runs(preprocessing_run_id,created_at);"""
class ModelRepository:
 def __init__(self,database_url=None):self.path=sqlite_path(database_url);self.path.parent.mkdir(parents=True,exist_ok=True);self.ensure_schema()
 def connect(self):connection=sqlite3.connect(self.path);connection.row_factory=sqlite3.Row;return connection
 def ensure_schema(self):
  with closing(self.connect()) as connection:connection.executescript(SCHEMA);connection.commit()
 def create(self,r):
  with closing(self.connect()) as connection:connection.execute("INSERT INTO model_runs VALUES(?,?,?,?,?,?,?,?,?)",(r["id"],r["preprocessing_run_id"],r["dataset_id"],r["status"],r["model_type"],json.dumps(r["configuration"]),json.dumps(r["summary"]),r["artifact_path"],r["created_at"]));connection.commit()
 def get(self,run_id):
  with closing(self.connect()) as connection:row=connection.execute("SELECT * FROM model_runs WHERE id=?",(run_id,)).fetchone();return self._decode(row) if row else None
 def list(self,preprocessing_run_id=None):
  with closing(self.connect()) as connection:rows=connection.execute("SELECT * FROM model_runs WHERE preprocessing_run_id=? ORDER BY created_at DESC",(preprocessing_run_id,)).fetchall() if preprocessing_run_id else connection.execute("SELECT * FROM model_runs ORDER BY created_at DESC").fetchall();return[self._decode(r) for r in rows]
 @staticmethod
 def _decode(row):value=dict(row);value["configuration"]=json.loads(value.pop("configuration_json"));value["summary"]=json.loads(value.pop("summary_json"));return value
