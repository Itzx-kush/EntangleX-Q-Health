from __future__ import annotations
from collections import Counter
from dataclasses import dataclass
import numpy as np
from imblearn.over_sampling import RandomOverSampler, SMOTE
from imblearn.under_sampling import RandomUnderSampler
from app.preprocessing.errors import PreprocessingError

@dataclass(frozen=True)
class ResamplingResult:
    features: np.ndarray
    labels: np.ndarray
    method: str
    rows_before: int
    rows_after: int
    rows_added: int
    rows_removed: int
    distribution_before: dict[str,int]
    distribution_after: dict[str,int]

def distribution(labels) -> dict[str,int]:
    return {str(key):int(value) for key,value in sorted(Counter(np.asarray(labels).tolist()).items(),key=lambda item:str(item[0]))}

def apply_resampling(features,labels,method:str,random_seed:int,smote_k_neighbors:int)->ResamplingResult:
    X=np.asarray(features);y=np.asarray(labels);before=distribution(y);rows_before=len(y)
    if len(before)!=2:raise PreprocessingError("RESAMPLING_REQUIRES_BINARY_TARGET","Resampling requires exactly two training classes.")
    if method=="none":resampled_X,resampled_y=X,y
    elif method=="random_over":resampled_X,resampled_y=RandomOverSampler(random_state=random_seed).fit_resample(X,y)
    elif method=="random_under":resampled_X,resampled_y=RandomUnderSampler(random_state=random_seed).fit_resample(X,y)
    elif method=="smote":
        minority=min(before.values())
        if minority<=smote_k_neighbors:raise PreprocessingError("SMOTE_INSUFFICIENT_MINORITY_SAMPLES","SMOTE requires more minority training samples than k-neighbors.",f"Minority samples: {minority}; requested neighbors: {smote_k_neighbors}.")
        resampled_X,resampled_y=SMOTE(random_state=random_seed,k_neighbors=smote_k_neighbors).fit_resample(X,y)
    else:raise PreprocessingError("UNSUPPORTED_RESAMPLING_METHOD","Unsupported resampling method.",method)
    rows_after=len(resampled_y)
    return ResamplingResult(np.asarray(resampled_X),np.asarray(resampled_y),method,rows_before,rows_after,max(0,rows_after-rows_before),max(0,rows_before-rows_after),before,distribution(resampled_y))
