from __future__ import annotations
import pandas as pd

def profile_frame(frame: pd.DataFrame) -> dict:
    numeric=[str(column) for column in frame.select_dtypes(include="number").columns]
    datetime=[str(column) for column in frame.select_dtypes(include=["datetime", "datetimetz"]).columns]
    categorical=[str(column) for column in frame.columns if str(column) not in numeric and str(column) not in datetime]
    missing={str(column):int(value) for column,value in frame.isna().sum().items()}
    return {"rows":int(frame.shape[0]),"columns":int(frame.shape[1]),"numeric_columns":numeric,"categorical_columns":categorical,"datetime_columns":datetime,"missing_values":missing,"total_missing_values":sum(missing.values()),"duplicate_rows":int(frame.duplicated().sum())}
