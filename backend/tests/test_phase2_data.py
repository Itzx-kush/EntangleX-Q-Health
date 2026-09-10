from __future__ import annotations

from io import BytesIO
from pathlib import Path
import tempfile
import unittest

import pandas as pd

from app.data.errors import DatasetError
from app.data.repository import DatasetRepository
from app.data.service import DatasetService


class PhaseTwoDataTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.service = DatasetService(
            DatasetRepository(f"sqlite:///{root / 'test.db'}"),
            root / "uploads",
            1,
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    @staticmethod
    def csv() -> bytes:
        return b"""feature,category,target
1,A,0
2,B,1
2,B,1
"""

    def test_csv_ingestion_profiles_and_hashes(self) -> None:
        summary = self.service.ingest("medical.csv", self.csv(), "text/csv")
        self.assertEqual(summary["rows"], 3)
        self.assertEqual(summary["columns"], 3)
        self.assertEqual(summary["numeric_columns"], ["feature", "target"])
        self.assertEqual(summary["categorical_columns"], ["category"])
        self.assertEqual(summary["duplicate_rows"], 1)
        self.assertEqual(len(summary["sha256"]), 64)

    def test_target_selection_requires_binary_target(self) -> None:
        summary = self.service.ingest("medical.csv", self.csv())
        selected = self.service.select_target(summary["id"], "target")
        self.assertEqual(selected["class_count"], 2)
        self.assertEqual(selected["class_distribution"], {"1": 2, "0": 1})

    def test_single_class_target_rejected(self) -> None:
        content = b"""x,target
1,1
2,1
"""
        with self.assertRaises(DatasetError) as context:
            self.service.ingest("one.csv", content, target_column="target")
        self.assertEqual(context.exception.code, "SINGLE_CLASS_TARGET")

    def test_empty_and_extension_rejected(self) -> None:
        invalid = (
            ("bad.txt", b"""a,b
1,2
""", "UNSUPPORTED_FILE_TYPE"),
            ("empty.csv", b"", "EMPTY_FILE"),
        )
        for name, content, code in invalid:
            with self.assertRaises(DatasetError) as context:
                self.service.ingest(name, content)
            self.assertEqual(context.exception.code, code)

    def test_missing_and_duplicate_analysis_does_not_repair(self) -> None:
        content = b"""a,b,target
1,,0
1,,0
2,x,1
"""
        summary = self.service.ingest("quality.csv", content)
        self.assertEqual(summary["total_missing_values"], 2)
        self.assertEqual(summary["duplicate_rows"], 1)
        self.assertTrue(any("no values were repaired" in item for item in summary["warnings"]))

    def test_xlsx_ingestion(self) -> None:
        frame = pd.DataFrame({"feature": [1, 2], "target": [0, 1]})
        buffer = BytesIO()
        frame.to_excel(buffer, index=False, engine="openpyxl")
        summary = self.service.ingest("medical.xlsx", buffer.getvalue())
        self.assertEqual(summary["rows"], 2)
        self.assertEqual(summary["extension"], ".xlsx")

    def test_preview_is_bounded_and_json_safe(self) -> None:
        summary = self.service.ingest("medical.csv", self.csv())
        preview = self.service.preview(summary["id"], 0, 2)
        self.assertEqual(len(preview["rows"]), 2)
        self.assertEqual(preview["total_rows"], 3)


if __name__ == "__main__":
    unittest.main()
