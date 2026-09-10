from __future__ import annotations
from io import BytesIO
from pathlib import Path
import pandas as pd
from app.data.errors import DatasetError

SUPPORTED_EXTENSIONS={".csv", ".xlsx"}

def normalized_extension(filename: str) -> str:
    extension=Path(filename).suffix.lower()
    if extension not in SUPPORTED_EXTENSIONS:
        raise DatasetError("UNSUPPORTED_FILE_TYPE", "Unsupported dataset file type.", "Upload a CSV or XLSX file.")
    return extension

def load_dataframe(content: bytes, extension: str) -> pd.DataFrame:
    try:
        if extension==".csv":
            frame=pd.read_csv(BytesIO(content))
        elif extension==".xlsx":
            frame=pd.read_excel(BytesIO(content), engine="openpyxl")
        else:
            raise DatasetError("UNSUPPORTED_FILE_TYPE", "Unsupported dataset file type.")
    except DatasetError:
        raise
    except Exception as exc:
        raise DatasetError("DATASET_PARSE_FAILED", "The uploaded dataset could not be parsed.", str(exc)) from exc
    if frame.empty or frame.shape[1]==0:
        raise DatasetError("EMPTY_DATASET", "The uploaded dataset is empty.", "At least one row and one column are required.")
    frame.columns=[str(column).strip() for column in frame.columns]
    if any(not column for column in frame.columns):
        raise DatasetError("INVALID_SCHEMA", "One or more columns have an empty name.")
    duplicates=frame.columns[frame.columns.duplicated()].tolist()
    if duplicates:
        raise DatasetError("DUPLICATE_COLUMNS", "Dataset contains duplicate column names.", ", ".join(duplicates))
    return frame

def load_dataframe_path(path: Path) -> pd.DataFrame:
    extension=normalized_extension(path.name)
    return load_dataframe(path.read_bytes(), extension)
