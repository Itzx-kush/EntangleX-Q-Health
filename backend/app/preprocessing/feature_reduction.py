from __future__ import annotations
from dataclasses import dataclass
from functools import partial
import numpy as np
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, VarianceThreshold, f_classif, f_regression, mutual_info_classif, mutual_info_regression
from app.preprocessing.errors import PreprocessingError


@dataclass(frozen=True)
class FeatureReductionResult:
    train: np.ndarray
    test: np.ndarray
    selected_feature_names: list[str]
    output_feature_names: list[str]
    selector: object | None
    reducer: object | None
    explained_variance_ratio: list[float]


def reduce_features(train, test, labels, feature_names, selection_method: str, feature_count: int, variance_threshold: float, reduction_method: str, pca_components: int, random_seed: int, task_type: str = "classification") -> FeatureReductionResult:
    train_values = np.asarray(train, dtype=float)
    test_values = np.asarray(test, dtype=float)
    names = list(feature_names)
    selector = None
    if selection_method == "variance":
        selector = VarianceThreshold(threshold=variance_threshold)
    elif selection_method in {"anova", "mutual_info"}:
        if feature_count > train_values.shape[1]:
            raise PreprocessingError("FEATURE_COUNT_TOO_LARGE", "Requested feature count exceeds available transformed features.", f"Requested {feature_count}; available {train_values.shape[1]}.")
        if selection_method == "anova":
            score = f_regression if task_type == "regression" else f_classif
        else:
            function = mutual_info_regression if task_type == "regression" else mutual_info_classif
            score = partial(function, random_state=random_seed)
        selector = SelectKBest(score_func=score, k=feature_count)
    elif selection_method != "none":
        raise PreprocessingError("UNSUPPORTED_FEATURE_SELECTION", "Unsupported feature-selection method.", selection_method)
    if selector is not None:
        try:
            train_values = selector.fit_transform(train_values, labels)
            test_values = selector.transform(test_values)
            names = [name for name, keep in zip(names, selector.get_support()) if keep]
        except Exception as exc:
            raise PreprocessingError("FEATURE_SELECTION_FAILED", "Feature selection failed.", str(exc)) from exc
    if train_values.shape[1] == 0:
        raise PreprocessingError("NO_FEATURES_SELECTED", "Feature selection removed every feature.")
    reducer = None
    variance = []
    output_names = names
    if reduction_method == "pca":
        limit = min(train_values.shape[0], train_values.shape[1])
        if pca_components > limit:
            raise PreprocessingError("PCA_COMPONENTS_TOO_LARGE", "PCA components exceed the train-only dimensional limit.", f"Requested {pca_components}; maximum {limit}.")
        reducer = PCA(n_components=pca_components, random_state=random_seed)
        try:
            train_values = reducer.fit_transform(train_values)
            test_values = reducer.transform(test_values)
        except Exception as exc:
            raise PreprocessingError("PCA_FAILED", "PCA fitting failed.", str(exc)) from exc
        variance = [round(float(value), 8) for value in reducer.explained_variance_ratio_]
        output_names = [f"PC{index + 1}" for index in range(pca_components)]
    elif reduction_method != "none":
        raise PreprocessingError("UNSUPPORTED_REDUCTION", "Unsupported dimensionality-reduction method.", reduction_method)
    return FeatureReductionResult(train_values, test_values, names, output_names, selector, reducer, variance)
