from __future__ import annotations
import importlib.util
from pathlib import Path
import tempfile
import unittest
SKLEARN_AVAILABLE=importlib.util.find_spec("sklearn") is not None
FASTAPI_AVAILABLE=importlib.util.find_spec("fastapi") is not None
@unittest.skipUnless(SKLEARN_AVAILABLE and FASTAPI_AVAILABLE,"Phase 3 API dependencies not installed")
class PhaseThreeApiTests(unittest.TestCase):
    def setUp(self)->None:
        from fastapi.testclient import TestClient
        from app.api.datasets import get_dataset_service
        from app.api.preprocessing import get_preprocessing_service
        from app.data.repository import DatasetRepository
        from app.data.service import DatasetService
        from app.main import app
        from app.preprocessing.repository import PreprocessingRepository
        from app.preprocessing.service import PreprocessingService
        self.app=app;self.temp=tempfile.TemporaryDirectory();root=Path(self.temp.name);datasets=DatasetRepository(f"sqlite:///{root/'api.db'}");ingestion=DatasetService(datasets,root/"uploads",2);preprocessing=PreprocessingService(datasets,PreprocessingRepository(f"sqlite:///{root/'api.db'}"),root/"uploads",root/"artifacts");app.dependency_overrides[get_dataset_service]=lambda:ingestion;app.dependency_overrides[get_preprocessing_service]=lambda:preprocessing;self.client=TestClient(app)
    def tearDown(self)->None:self.client.close();self.app.dependency_overrides.clear();self.temp.cleanup()
    def test_preprocessing_run_api(self)->None:
        rows=["age,group,target"];rows.extend(f"{30+i},{'A' if i%2 else 'B'},{i%2}" for i in range(30));content=("\n".join(rows)+"\n").encode();uploaded=self.client.post("/api/datasets/upload",files={"file":("study.csv",content,"text/csv")});self.assertEqual(uploaded.status_code,201,uploaded.text);dataset_id=uploaded.json()["id"];selected=self.client.post(f"/api/datasets/{dataset_id}/target",json={"target_column":"target"});self.assertEqual(selected.status_code,200,selected.text);response=self.client.post("/api/preprocessing/run",json={"dataset_id":dataset_id,"random_seed":42});self.assertEqual(response.status_code,201,response.text);body=response.json();self.assertEqual(body["fitted_on"],"training_only");self.assertGreater(body["output_features"],0);self.assertEqual(self.client.get(f"/api/preprocessing/runs/{body['id']}").status_code,200)
    def test_target_required_error_is_structured(self)->None:
        uploaded=self.client.post("/api/datasets/upload",files={"file":("study.csv",b"x,target\n1,0\n2,1\n","text/csv")});response=self.client.post("/api/preprocessing/run",json={"dataset_id":uploaded.json()["id"]});self.assertEqual(response.status_code,400);self.assertEqual(response.json()["error"],"TARGET_REQUIRED")
if __name__=="__main__":unittest.main()
