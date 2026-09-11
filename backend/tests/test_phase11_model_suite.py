import importlib.util
import unittest
import numpy as np
from pydantic import ValidationError
from app.data.validator import analyze_target
from app.quantum.model_utils import bounded_subset, fidelity_kernel
from app.quantum.qml_schemas import QNNRequest, QSVMRequest, VQCRequest


class PhaseElevenContractTests(unittest.TestCase):
    def test_model_configuration_bounds_and_optimizer_choices(self):
        with self.assertRaises(ValidationError):
            QSVMRequest(encoding_run_id="x", training_samples=65)
        with self.assertRaises(ValidationError):
            QNNRequest(encoding_run_id="x", ansatz_reps=5)
        self.assertEqual(VQCRequest(encoding_run_id="x", optimizer="nelder_mead").optimizer, "nelder_mead")
        self.assertEqual(QNNRequest(encoding_run_id="x", task_type="regression").task_type, "regression")

    def test_bounded_classification_subset_preserves_both_classes(self):
        X = np.arange(120, dtype=float).reshape(40, 3)
        y = np.asarray([0] * 36 + [1] * 4)
        selected_X, selected_y = bounded_subset(X, y, 12, 42, "classification")
        self.assertEqual(len(selected_X), 12)
        self.assertEqual(set(selected_y.tolist()), {0, 1})

    def test_fidelity_kernel_depends_on_quantum_states(self):
        basis = np.asarray([[1, 0], [0, 1]], dtype=complex)
        superposition = np.asarray([[1, 0], [1 / np.sqrt(2), 1 / np.sqrt(2)]], dtype=complex)
        first = fidelity_kernel(basis, basis)
        second = fidelity_kernel(superposition, superposition)
        self.assertFalse(np.allclose(first, second))
        self.assertTrue(np.allclose(np.diag(first), 1.0))
        self.assertTrue(np.allclose(np.diag(second), 1.0))

    def test_regression_target_analysis_is_numeric_and_continuous(self):
        import pandas as pd
        frame = pd.DataFrame({"feature": range(12), "risk": np.linspace(0.1, 2.0, 12)})
        result = analyze_target(frame, "risk", "regression")
        self.assertEqual(result["task_type"], "regression")
        self.assertAlmostEqual(result["target_min"], 0.1)
        self.assertAlmostEqual(result["target_max"], 2.0)
        self.assertIsNone(result["class_count"])


DEPENDENCIES_AVAILABLE = all(importlib.util.find_spec(name) is not None for name in ("joblib", "sklearn", "imblearn"))


@unittest.skipUnless(DEPENDENCIES_AVAILABLE, "Phase 11 preprocessing dependencies not installed")
class PhaseElevenRegressionPipelineTests(unittest.TestCase):
    def test_regression_rejects_class_resampling(self):
        from app.preprocessing.resampling import apply_resampling
        with self.assertRaises(Exception) as context:
            apply_resampling(np.ones((8, 2)), np.arange(8, dtype=float), "smote", 42, 3, "regression")
        self.assertEqual(context.exception.code, "REGRESSION_RESAMPLING_UNSUPPORTED")

    def test_regression_preprocessing_is_train_only_and_persisted(self):
        import joblib
        import tempfile
        from pathlib import Path
        from app.data.repository import DatasetRepository
        from app.data.service import DatasetService
        from app.preprocessing.repository import PreprocessingRepository
        from app.preprocessing.schemas import PreprocessingConfig
        from app.preprocessing.service import PreprocessingService
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database = f"sqlite:///{root / 'test.db'}"
            datasets = DatasetRepository(database)
            ingestion = DatasetService(datasets, root / "uploads", 2)
            rows = ["age,marker,group,risk"]
            rows.extend(f"{20+i},{1+(i%7)},{'A' if i%2 else 'B'},{0.2*i + (i%3)*0.05}" for i in range(50))
            dataset = ingestion.ingest("regression.csv", ("\n".join(rows) + "\n").encode())
            selected = ingestion.select_target(dataset["id"], "risk", "regression")
            service = PreprocessingService(datasets, PreprocessingRepository(database), root / "uploads", root / "artifacts")
            run = service.run(PreprocessingConfig(dataset_id=dataset["id"], task_type="regression", resampling_method="none", feature_selection_method="anova", feature_count=2))
            self.assertEqual(run["task_type"], "regression")
            self.assertEqual(run["resampling_method"], "none")
            artifact = joblib.load(root / "artifacts" / f"{run['id']}.joblib")
            self.assertEqual(artifact["task_type"], "regression")
            self.assertEqual(artifact["fitted_on"], "training_only")
            self.assertTrue(np.issubdtype(np.asarray(artifact["training_labels"]).dtype, np.floating))
            self.assertEqual(selected["task_type"], "regression")


@unittest.skipUnless(importlib.util.find_spec("qiskit"), "Qiskit not installed")
class PhaseElevenQuantumExecutionTests(unittest.TestCase):
    def test_feature_map_and_qnn_outputs_change_with_inputs(self):
        from app.quantum.model_utils import feature_states, fidelity_kernel
        from app.quantum.qnn import QNNService
        X = np.asarray([[0.1, 0.2], [1.0, 0.7], [2.0, 0.4]])
        states = feature_states(X, "linear")
        kernel = fidelity_kernel(states, states)
        self.assertTrue(np.allclose(np.diag(kernel), 1.0))
        self.assertFalse(np.allclose(kernel, np.ones_like(kernel)))
        parameters = np.asarray([0.1, 0.2, 0.3, -0.2, 0.05])
        first = QNNService.raw_prediction(X[0], parameters, 1, "linear")
        second = QNNService.raw_prediction(X[1], parameters, 1, "linear")
        shifted = QNNService.raw_prediction(X[0], parameters + 0.3, 1, "linear")
        self.assertFalse(np.isclose(first, second))
        self.assertFalse(np.isclose(first, shifted))


if __name__ == "__main__":
    unittest.main()
