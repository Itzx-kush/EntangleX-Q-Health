"""Dependency-free Phase 1 validation server.
Use Uvicorn + app.main:app in the target runtime. This harness exists only because
this sandbox cannot download FastAPI/Uvicorn; it exercises the same health service.
"""
from __future__ import annotations
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from app.services.health import build_health_payload

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path not in {"/health", "/api/v1/health"}:
            self.send_response(404); self.send_header("Content-Type", "application/json"); self.end_headers(); self.wfile.write(b'{"error":"NOT_FOUND","message":"Route not found."}'); return
        body=json.dumps(build_health_payload()).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Access-Control-Allow-Origin", "http://localhost:5173"); self.send_header("Content-Length", str(len(body))); self.end_headers(); self.wfile.write(body)
    def log_message(self, fmt, *args): pass

if __name__ == "__main__":
    ThreadingHTTPServer(("127.0.0.1", 8000), Handler).serve_forever()
