import json
import logging
import sys
from datetime import datetime, timezone

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"timestamp": datetime.now(timezone.utc).isoformat(), "level": record.levelname, "logger": record.name, "message": record.getMessage()}
        for key in ("experiment_id", "job_id", "model_type", "quantum_backend"):
            value = getattr(record, key, None)
            if value is not None: payload[key] = value
        if record.exc_info: payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)

def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(logging.INFO)
