import json,sqlite3
from contextlib import closing
from app.storage.database import sqlite_path
SCHEMA='CREATE TABLE IF NOT EXISTS model_runs(id TEXT PRIMARY KEY,preprocessing_run_id TEXT,dataset_id TEXT,status TEXT,model_type TEXT,configuration_json TEXT,summary_json TEXT,artifact_path TEXT,created_at TEXT)'
class ModelRepository:
 def __init__(self,database_url=None):self.path=sqlite_path(database_url);self.path.parent.mkdir(parents=True,exist_ok=True);self.ensure_schema()
 def connect(self):c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row;return c
 def ensure_schema(self):
  with closing(self.connect()) as c:c.execute(SCHEMA);c.commit()
 def create(self,r):
  with closing(self.connect()) as c:c.execute('INSERT INTO model_runs VALUES(?,?,?,?,?,?,?,?,?)',(r['id'],r['preprocessing_run_id'],r['dataset_id'],r['status'],r['model_type'],json.dumps(r['configuration']),json.dumps(r['summary']),r['artifact_path'],r['created_at']));c.commit()
 def get(self,i):
  with closing(self.connect()) as c:x=c.execute('SELECT * FROM model_runs WHERE id=?',(i,)).fetchone();return self._d(x) if x else None
 def list(self,p=None):
  with closing(self.connect()) as c:rows=c.execute('SELECT * FROM model_runs WHERE preprocessing_run_id=?',(p,)).fetchall() if p else c.execute('SELECT * FROM model_runs').fetchall();return[self._d(x) for x in rows]
 @staticmethod
 def _d(x):r=dict(x);r['configuration']=json.loads(r.pop('configuration_json'));r['summary']=json.loads(r.pop('summary_json'));return r
