import json,sqlite3
from contextlib import closing
from app.storage.database import sqlite_path
SCHEMA='CREATE TABLE IF NOT EXISTS quantum_runs(id TEXT PRIMARY KEY,backend TEXT,execution_mode TEXT,configuration_json TEXT,resources_json TEXT,counts_json TEXT,execution_duration_seconds REAL,artifact_path TEXT,created_at TEXT)'
class QuantumRunRepository:
 def __init__(self,database_url=None):self.path=sqlite_path(database_url);self.path.parent.mkdir(parents=True,exist_ok=True);self.ensure_schema()
 def connect(self):c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row;return c
 def ensure_schema(self):
  with closing(self.connect()) as c:c.execute(SCHEMA);c.commit()
 def create(self,r):
  with closing(self.connect()) as c:c.execute('INSERT INTO quantum_runs VALUES(?,?,?,?,?,?,?,?,?)',(r['id'],r['backend'],r['execution_mode'],json.dumps(r['configuration']),json.dumps(r['resources']),json.dumps(r['measurement_counts']),r['execution_duration_seconds'],r['artifact_path'],r['created_at']));c.commit()
 def get(self,i):
  with closing(self.connect()) as c:x=c.execute('SELECT * FROM quantum_runs WHERE id=?',(i,)).fetchone();return self._d(x) if x else None
 def list(self):
  with closing(self.connect()) as c:return[self._d(x) for x in c.execute('SELECT * FROM quantum_runs ORDER BY created_at DESC').fetchall()]
 @staticmethod
 def _d(x):r=dict(x);r['configuration']=json.loads(r.pop('configuration_json'));r['resources']=json.loads(r.pop('resources_json'));r['measurement_counts']=json.loads(r.pop('counts_json'));return r
