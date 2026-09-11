import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.core.config import Settings
from app.services.capabilities import runtime_capabilities
from app.storage.database import check_database

class PhaseOneTests(unittest.TestCase):
    def test_settings_guard_qubits(self):
        with patch.dict(os.environ, {"DEFAULT_QUBITS":"4", "MAX_QUBITS":"8"}): Settings().validate()
    def test_sqlite_health(self):
        with tempfile.TemporaryDirectory() as tmp:
            ok, error=check_database(f"sqlite:///{Path(tmp)/'test.db'}")
            self.assertTrue(ok); self.assertIsNone(error)
    def test_capabilities_are_explicit(self):
        payload=runtime_capabilities()
        self.assertIn(payload["quantum_simulator"], {"available","unavailable"})
        self.assertIn("qiskit", payload["packages"])
    def test_no_fake_metrics_in_frontend(self):
        source=(Path(__file__).parents[2]/"frontend/src/App.tsx").read_text()
        for fake in ("accuracy = 0.94", "92.1%", "88.7%"):
            self.assertNotIn(fake, source)

if __name__ == "__main__": unittest.main()
