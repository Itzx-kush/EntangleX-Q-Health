import json,sqlite3
from contextlib import closing
from app.storage.database import sqlite_path
SCHEMA='''CREATE TABLE IF NOT EXISTS quantum_encoding_runs(id TEXT PRIMARY KEY,preprocessing_run_id TEXT,dataset_id TEXT,configuration_json TEXT,summary_json TEXT,artifact_path TEXT,created_at TEXT);CREATE INDEX IF NOT EXISTS idx_encoding_preprocessing ON quantum_encoding_runs(preprocessing_run_id,created_at);CREATE TABLE IF NOT EXISTS vqc_runs(id TEXT PRIMARY KEY,encoding_run_id TEXT,preprocessing_run_id TEXT,dataset_id TEXT,status TEXT,configuration_json TEXT,summary_json TEXT,artifact_path TEXT,created_at TEXT);CREATE INDEX IF NOT EXISTS idx_vqc_encoding ON vqc_runs(encoding_run_id,created_at);'''
class QMLRepository:
 def __init__(self,database_url=None):self.path=sqlite_path(database_url);self.path.parent.mkdir(parents=True,exist_ok=True);self.ensure_schema()
 def connect(self):c=sqlite3.connect(self.path);c.row_factory=sqlite3.Row;return c
 def ensure_schema(self):
  with closing(self.connect()) as c:c.executescript(SCHEMA);c.commit()
 def create_encoding(self,r):
  with closing(self.connect()) as c:c.execute('INSERT INTO quantum_encoding_runs VALUES(?,?,?,?,?,?,?)',(r['id'],r['preprocessing_run_id'],r['dataset_id'],json.dumps(r['configuration']),json.dumps(r['summary']),r['artifact_path'],r['created_at']));c.commit()
 def get_encoding(self,i):
  with closing(self.connect()) as c:x=c.execute('SELECT * FROM quantum_encoding_runs WHERE id=?',(i,)).fetchone();return self._decode(x) if x else None
 def create_vqc(self,r):
  with closing(self.connect()) as c:c.execute('INSERT INTO vqc_runs VALUES(?,?,?,?,?,?,?,?,?)',(r['id'],r['encoding_run_id'],r['preprocessing_run_id'],r['dataset_id'],r['status'],json.dumps(r['configuration']),json.dumps(r['summary']),r['artifact_path'],r['created_at']));c.commit()
 def get_vqc(self,i):
  with closing(self.connect()) as c:x=c.execute('SELECT * FROM vqc_runs WHERE id=?',(i,)).fetchone();return self._decode(x) if x else None
 @staticmethod
 def _decode(x):r=dict(x);r['configuration']=json.loads(r.pop('configuration_json'));r['summary']=json.loads(r.pop('summary_json'));return r
