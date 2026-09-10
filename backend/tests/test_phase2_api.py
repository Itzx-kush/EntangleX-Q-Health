from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from fastapi.testclient import TestClient

from app.api.datasets import get_dataset_service
from app.data.repository import DatasetRepository
from app.data.service import DatasetService
from app.main import app


class PhaseTwoApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.service = DatasetService(DatasetRepository(f"sqlite:///{root / 'api.db'}"), root / "uploads", 1)
        app.dependency_overrides[get_dataset_service] = lambda: self.service
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.client.close()
        app.dependency_overrides.clear()
        self.temp.cleanup()

    def test_upload_list_target_and_preview(self) -> None:
        content = b"""feature,target
1,0
2,1
"""
        response = self.client.post("/api/datasets/upload", files={"file": ("medical.csv", content, "text/csv")})
        self.assertEqual(response.status_code, 201, response.text)
        dataset_id = response.json()["id"]
        self.assertEqual(self.client.get("/api/datasets").json()["total"], 1)
        target = self.client.post(f"/api/datasets/{dataset_id}/target", json={"target_column": "target"})
        self.assertEqual(target.status_code, 200)
        self.assertEqual(target.json()["class_count"], 2)
        preview = self.client.post(f"/api/datasets/{dataset_id}/preview", json={"limit": 1, "offset": 0})
        self.assertEqual(preview.status_code, 200)
        self.assertEqual(len(preview.json()["rows"]), 1)

    def test_structured_validation_error(self) -> None:
        response = self.client.post("/api/datasets/upload", files={"file": ("bad.txt", b"x\n1\n", "text/plain")})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json()["error"], "UNSUPPORTED_FILE_TYPE")


if __name__ == "__main__":
    unittest.main()
