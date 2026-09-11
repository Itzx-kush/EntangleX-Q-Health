from __future__ import annotations
import math
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from app.data.errors import DatasetError
from app.data.loader import normalized_extension

ALLOWED_SCALAR_KINDS={"b", "i", "u", "f", "c", "m", "M", "O", "S", "U"}

def validate_upload(filename: str | None, content: bytes, max_size_mb: int) -> str:
    if not filename or not Path(filename).name:
        raise DatasetError("MISSING_FILENAME", "The upload must include a filename.")
    extension=normalized_extension(Path(filename).name)
    if not content:
        raise DatasetError("EMPTY_FILE", "The uploaded file is empty.")
    max_bytes=max_size_mb*1024*1024
    if len(content)>max_bytes:
        raise DatasetError("FILE_TOO_LARGE", "The uploaded file exceeds the configured size limit.", f"Maximum size is {max_size_mb} MB.", 413)
    return extension

def validate_frame(frame: pd.DataFrame) -> list[str]:
    warnings=[]
    unsupported=[str(column) for column in frame.columns if frame[column].dtype.kind not in ALLOWED_SCALAR_KINDS]
    if unsupported:
        raise DatasetError("UNSUPPORTED_DATA_TYPE", "Dataset contains unsupported column types.", ", ".join(unsupported))
    numeric=frame.select_dtypes(include=[np.number])
    if not numeric.empty:
        infinite_columns=[str(column) for column in numeric.columns if np.isinf(numeric[column].to_numpy(dtype=float, na_value=np.nan)).any()]
        if infinite_columns:
            raise DatasetError("INFINITE_VALUES", "Dataset contains infinite numerical values.", ", ".join(infinite_columns))
    duplicate_rows=int(frame.duplicated().sum())
    if duplicate_rows:
        warnings.append(f"Dataset contains {duplicate_rows} duplicate row(s); no rows were removed.")
    missing=int(frame.isna().sum().sum())
    if missing:
        warnings.append(f"Dataset contains {missing} missing value(s); no values were repaired.")
    return warnings

def analyze_target(frame: pd.DataFrame, target_column: str, task_type: str = "classification") -> dict[str, Any]:
    if target_column not in frame.columns:
        raise DatasetError("TARGET_NOT_FOUND", "The selected target column does not exist.", target_column)
    target = frame[target_column]
    if target.isna().any():
        raise DatasetError("TARGET_HAS_MISSING_VALUES", "Target column contains missing values.", "Choose another target or resolve missing target rows before training.")
    if task_type == "regression":
        numeric = pd.to_numeric(target, errors="coerce")
        if numeric.isna().any() or not np.isfinite(numeric.to_numpy(dtype=float)).all():
            raise DatasetError("REGRESSION_TARGET_NOT_NUMERIC", "Regression requires a finite numeric target column.", target_column)
        if numeric.nunique() < 3:
            raise DatasetError("REGRESSION_TARGET_NOT_CONTINUOUS", "Regression requires at least three distinct target values.")
        warnings = []
        if numeric.nunique() < 10:
            warnings.append("Regression target has fewer than 10 distinct values; inspect whether classification is more appropriate.")
        return {
            "task_type": "regression", "class_distribution": None, "class_proportions": None,
            "class_count": None, "imbalance_ratio": None, "target_min": float(numeric.min()),
            "target_max": float(numeric.max()), "target_mean": float(numeric.mean()),
            "target_std": float(numeric.std(ddof=0)), "warnings": warnings,
        }
    if task_type != "classification":
        raise DatasetError("UNSUPPORTED_TASK_TYPE", "Task type must be classification or regression.", task_type)
    counts = target.value_counts(dropna=False)
    if len(counts) < 2:
        raise DatasetError("SINGLE_CLASS_TARGET", "Target column contains only one class. Binary classification requires exactly two classes.")
    if len(counts) > 2:
        raise DatasetError("NON_BINARY_TARGET", "Target column is not binary.", f"Found {len(counts)} distinct classes; expected exactly two.")
    distribution = {str(key): int(value) for key, value in counts.items()}
    total = int(counts.sum())
    proportions = {key: round(value / total, 6) for key, value in distribution.items()}
    minimum = min(distribution.values())
    maximum = max(distribution.values())
    ratio = round(maximum / minimum, 4) if minimum else math.inf
    warnings = []
    if ratio >= 4:
        warnings.append(f"Target is highly imbalanced ({ratio}:1 majority-to-minority ratio). No resampling was applied.")
    return {
        "task_type": "classification", "class_distribution": distribution, "class_proportions": proportions,
        "class_count": 2, "imbalance_ratio": ratio, "target_min": None, "target_max": None,
        "target_mean": None, "target_std": None, "warnings": warnings,
    }
