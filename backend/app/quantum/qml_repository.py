import json
import sqlite3
from contextlib import closing
from app.storage.database import sqlite_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS quantum_encoding_runs(
 id TEXT PRIMARY KEY, preprocessing_run_id TEXT, dataset_id TEXT,
 configuration_json TEXT, summary_json TEXT, artifact_path TEXT, created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_encoding_preprocessing ON quantum_encoding_runs(preprocessing_run_id,created_at);
CREATE TABLE IF NOT EXISTS vqc_runs(
 id TEXT PRIMARY KEY, encoding_run_id TEXT, preprocessing_run_id TEXT, dataset_id TEXT, status TEXT,
 configuration_json TEXT, summary_json TEXT, artifact_path TEXT, created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_vqc_encoding ON vqc_runs(encoding_run_id,created_at);
CREATE TABLE IF NOT EXISTS quantum_model_runs(
 id TEXT PRIMARY KEY, model_type TEXT NOT NULL, task_type TEXT NOT NULL,
 encoding_run_id TEXT NOT NULL, preprocessing_run_id TEXT NOT NULL, dataset_id TEXT NOT NULL, status TEXT NOT NULL,
 configuration_json TEXT NOT NULL, summary_json TEXT NOT NULL, artifact_path TEXT NOT NULL, created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_quantum_models_encoding ON quantum_model_runs(encoding_run_id,model_type,created_at);
"""


class QMLRepository:
    def __init__(self, database_url=None):
        self.path = sqlite_path(database_url)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.ensure_schema()

    def connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def ensure_schema(self):
        with closing(self.connect()) as connection:
            connection.executescript(SCHEMA)
            connection.commit()

    def create_encoding(self, record):
        with closing(self.connect()) as connection:
            connection.execute("INSERT INTO quantum_encoding_runs VALUES(?,?,?,?,?,?,?)", (
                record["id"], record["preprocessing_run_id"], record["dataset_id"], json.dumps(record["configuration"]),
                json.dumps(record["summary"]), record["artifact_path"], record["created_at"],
            ))
            connection.commit()

    def get_encoding(self, run_id):
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM quantum_encoding_runs WHERE id=?", (run_id,)).fetchone()
            return self._decode(row) if row else None

    def create_vqc(self, record):
        with closing(self.connect()) as connection:
            connection.execute("INSERT INTO vqc_runs VALUES(?,?,?,?,?,?,?,?,?)", (
                record["id"], record["encoding_run_id"], record["preprocessing_run_id"], record["dataset_id"],
                record["status"], json.dumps(record["configuration"]), json.dumps(record["summary"]),
                record["artifact_path"], record["created_at"],
            ))
            connection.commit()

    def get_vqc(self, run_id):
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT * FROM vqc_runs WHERE id=?", (run_id,)).fetchone()
            return self._decode(row) if row else None

    def create_model(self, record):
        with closing(self.connect()) as connection:
            connection.execute("INSERT INTO quantum_model_runs VALUES(?,?,?,?,?,?,?,?,?,?,?)", (
                record["id"], record["model_type"], record["task_type"], record["encoding_run_id"],
                record["preprocessing_run_id"], record["dataset_id"], record["status"],
                json.dumps(record["configuration"]), json.dumps(record["summary"]), record["artifact_path"], record["created_at"],
            ))
            connection.commit()

    def get_model(self, run_id, model_type=None):
        query = "SELECT * FROM quantum_model_runs WHERE id=?"
        params = [run_id]
        if model_type:
            query += " AND model_type=?"
            params.append(model_type)
        with closing(self.connect()) as connection:
            row = connection.execute(query, params).fetchone()
            return self._decode(row) if row else None

    def list_models(self, encoding_run_id=None):
        query = "SELECT * FROM quantum_model_runs"
        params = []
        if encoding_run_id:
            query += " WHERE encoding_run_id=?"
            params.append(encoding_run_id)
        query += " ORDER BY created_at DESC"
        with closing(self.connect()) as connection:
            return [self._decode(row) for row in connection.execute(query, params).fetchall()]

    @staticmethod
    def _decode(row):
        record = dict(row)
        record["configuration"] = json.loads(record.pop("configuration_json"))
        record["summary"] = json.loads(record.pop("summary_json"))
        return record
