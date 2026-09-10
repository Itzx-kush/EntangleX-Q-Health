import json,sqlite3
from contextlib import closing
from app.storage.database import sqlite_path
SCHEMA='CREATE TABLE IF NOT EXISTS evaluation_runs(id TEXT PRIMARY KEY,model_run_id TEXT,preprocessing_run_id TEXT,dataset_id TEXT,model_type TEXT,status TEXT,metrics_json TEXT,artifact_path TEXT,created_at TEXT)'
class EvaluationRepository:
 def __init__(self,database_url=None):self.path=sqlite_path(database_url);self.path.parent.mkdir(parents=True,exist_ok=True);self.ensure_schema()
 def connect(self):c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row;return c
 def ensure_schema(self):
  with closing(self.connect()) as c:c.execute(SCHEMA);c.commit()
 def create(self,r):
  with closing(self.connect()) as c:c.execute('INSERT INTO evaluation_runs VALUES(?,?,?,?,?,?,?,?,?)',(r['id'],r['model_run_id'],r['preprocessing_run_id'],r['dataset_id'],r['model_type'],r['status'],json.dumps(r['metrics']),r['artifact_path'],r['created_at']));c.commit()
 def get(self,i):
  with closing(self.connect()) as c:x=c.execute('SELECT * FROM evaluation_runs WHERE id=?',(i,)).fetchone();return self._d(x) if x else None
 def list(self,m=None):
  with closing(self.connect()) as c:rows=c.execute('SELECT * FROM evaluation_runs WHERE model_run_id=?',(m,)).fetchall() if m else c.execute('SELECT * FROM evaluation_runs').fetchall();return[self._d(x) for x in rows]
 @staticmethod
 def _d(x):r=dict(x);r['metrics']=json.loads(r.pop('metrics_json'));return r
