from __future__ import annotations
import numpy as np
import pandas as pd

class OutlierPolicy:
    def __init__(self, method: str | None, threshold: float) -> None:
        self.method=method; self.threshold=threshold; self.bounds:dict[str,tuple[float,float]]={}
    def fit(self, frame: pd.DataFrame) -> "OutlierPolicy":
        self.bounds={}
        if self.method is None:return self
        for column in frame.select_dtypes(include="number").columns:
            series=frame[column].dropna().astype(float)
            if series.empty:continue
            if self.method=="iqr":
                q1,q3=series.quantile([0.25,0.75]); spread=float(q3-q1); low=float(q1-self.threshold*spread); high=float(q3+self.threshold*spread)
            elif self.method=="zscore":
                mean=float(series.mean()); std=float(series.std(ddof=0)); low,high=(mean-self.threshold*std,mean+self.threshold*std) if std else (-np.inf,np.inf)
            else:raise ValueError(f"Unsupported outlier method: {self.method}")
            self.bounds[str(column)]=(low,high)
        return self
    def clip(self, frame: pd.DataFrame) -> pd.DataFrame:
        result=frame.copy()
        for column,(low,high) in self.bounds.items():result[column]=result[column].clip(lower=low,upper=high)
        return result
    def inlier_mask(self, frame: pd.DataFrame) -> pd.Series:
        mask=pd.Series(True,index=frame.index)
        for column,(low,high) in self.bounds.items():mask &= frame[column].isna() | frame[column].between(low,high,inclusive="both")
        return mask
