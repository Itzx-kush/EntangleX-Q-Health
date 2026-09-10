from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

from app.data.repository import DatasetRepository
from app.data.service import DatasetService
from app.preprocessing.errors import PreprocessingError
from app.preprocessing.repository import PreprocessingRepository

SKLEARN_AVAILABLE = importlib.util.find_spec("sklearn") is not None

@unittest.skipUnless(SKLEARN_AVAILABLE, "scikit-learn not installed")
class PhaseThreePreprocessingTests(unittest.TestCase):
    def setUp(self) -> None:
        from app.preprocessing.service import PreprocessingService
        self.temp = tempfile.TemporaryDirectory(); root = Path(self.temp.name)
        self.datasets = DatasetRepository(f"sqlite:///{root / 'test.db'}")
        self.ingestion = DatasetService(self.datasets, root / "uploads", 2)
        self.service = PreprocessingService(self.datasets, PreprocessingRepository(f"sqlite:///{root / 'test.db'}"), root / "uploads", root / "artifacts")
    def tearDown(self) -> None:self.temp.cleanup()
    def dataset(self) -> dict:
        rows=["age,marker,group,target"]; rows.extend(f"{30+i},{1+i%5},{'A' if i%2 else 'B'},{i%2}" for i in range(40)); rows.append("69,5,A,1")
        summary=self.ingestion.ingest("study.csv",("\n".join(rows)+"\n").encode()); return self.ingestion.select_target(summary["id"],"target")
    def test_pipeline_is_fitted_on_training_only_and_persisted(self) -> None:
        import joblib
        from app.preprocessing.schemas import PreprocessingConfig
        dataset=self.dataset(); result=self.service.run(PreprocessingConfig(dataset_id=dataset["id"],duplicate_mode="remove",categorical_encoding="one_hot",scaling="standard"))
        self.assertEqual(result["fitted_on"],"training_only"); self.assertEqual(result["duplicates_removed"],1); self.assertGreater(result["output_features"],result["input_features"])
        bundle=joblib.load(self.service.artifact_dir/f"{result['id']}.joblib"); self.assertEqual(bundle["fitted_on"],"training_only")
    def test_target_is_required(self) -> None:
        from app.preprocessing.schemas import PreprocessingConfig
        summary=self.ingestion.ingest("study.csv",b"x,target\n1,0\n2,1\n")
        with self.assertRaises(PreprocessingError) as context:self.service.run(PreprocessingConfig(dataset_id=summary["id"]))
        self.assertEqual(context.exception.code,"TARGET_REQUIRED")
if __name__=="__main__":unittest.main()
