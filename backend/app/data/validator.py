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

def analyze_target(frame: pd.DataFrame, target_column: str) -> dict[str, Any]:
    if target_column not in frame.columns:
        raise DatasetError("TARGET_NOT_FOUND", "The selected target column does not exist.", target_column)
    target=frame[target_column]
    if target.isna().any():
        raise DatasetError("TARGET_HAS_MISSING_VALUES", "Target column contains missing values.", "Choose another target or resolve missing targets in a later preprocessing step.")
    counts=target.value_counts(dropna=False)
    if len(counts)<2:
        raise DatasetError("SINGLE_CLASS_TARGET", "Target column contains only one class. Binary classification requires exactly two classes.")
    if len(counts)>2:
        raise DatasetError("NON_BINARY_TARGET", "Target column is not binary.", f"Found {len(counts)} distinct classes; expected exactly two.")
    distribution={str(key):int(value) for key,value in counts.items()}
    total=int(counts.sum())
    proportions={key:round(value/total,6) for key,value in distribution.items()}
    minimum=min(distribution.values()); maximum=max(distribution.values())
    ratio=round(maximum/minimum,4) if minimum else math.inf
    warnings=[]
    if ratio>=4:
        warnings.append(f"Target is highly imbalanced ({ratio}:1 majority-to-minority ratio). No resampling was applied.")
    return {"class_distribution":distribution,"class_proportions":proportions,"class_count":2,"imbalance_ratio":ratio,"warnings":warnings}
