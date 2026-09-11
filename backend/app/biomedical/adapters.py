from app.orchestration.errors import OrchestrationError
from app.orchestration.schemas import BiomedicalValidationRequest, BiomedicalValidationResult


def _samples(value: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise OrchestrationError("INVALID_SAMPLE_COUNT", "samples must be an integer greater than zero.", {"samples": value})
    return value


def validate_ehr(request: BiomedicalValidationRequest) -> BiomedicalValidationResult:
    columns = request.columns or []
    if not columns:
        raise OrchestrationError("INVALID_EHR_SCHEMA", "EHR validation requires a non-empty columns array.", {"required": "columns"})
    names: list[str] = []
    kinds = {"numeric": 0, "categorical": 0, "datetime": 0, "text": 0}
    for column in columns:
        if not isinstance(column, dict) or not isinstance(column.get("name"), str) or not column["name"].strip():
            raise OrchestrationError("INVALID_EHR_COLUMN", "Every EHR column requires a non-empty name.", {"column": column})
        kind = column.get("kind", "numeric")
        if kind not in kinds:
            raise OrchestrationError("INVALID_EHR_COLUMN_TYPE", "EHR column kind must be numeric, categorical, datetime or text.", {"kind": kind})
        names.append(column["name"])
        kinds[kind] += 1
    if request.target_column and request.target_column not in names:
        raise OrchestrationError("TARGET_COLUMN_NOT_FOUND", "The target column is not present in the EHR schema.", {"target_column": request.target_column})
    features = len(names) - (1 if request.target_column else 0)
    if features < 1:
        raise OrchestrationError("NO_PREDICTOR_FEATURES", "At least one predictor feature is required.", {})
    return BiomedicalValidationResult(modality="ehr", valid=True, normalized={"modality": "ehr", "samples": _samples(request.samples), "feature_count": features, "feature_names": names, "target_column": request.target_column, "column_kinds": kinds, "representation": "structured_tabular"})


def validate_genomics(request: BiomedicalValidationRequest) -> BiomedicalValidationResult:
    if request.features is None:
        raise OrchestrationError("FEATURE_COUNT_REQUIRED", "Genomics validation requires a feature count.", {})
    if request.numeric is not True:
        raise OrchestrationError("INVALID_GENOMICS_MATRIX", "The genomics feature matrix must be numeric before preprocessing.", {"numeric": request.numeric})
    if request.feature_names is not None and len(request.feature_names) != request.features:
        raise OrchestrationError("FEATURE_NAME_COUNT_MISMATCH", "feature_names must match the genomic feature count.", {"features": request.features, "feature_names": len(request.feature_names)})
    warnings = []
    if request.features > 64:
        warnings.append("High-dimensional genomic matrices should use feature selection or dimensionality reduction before quantum encoding.")
    return BiomedicalValidationResult(modality="genomics", valid=True, normalized={"modality": "genomics", "samples": _samples(request.samples), "feature_count": request.features, "feature_names": request.feature_names, "target_column": request.target_column, "representation": "numeric_feature_matrix"}, warnings=warnings)


def validate_medical_image(request: BiomedicalValidationRequest) -> BiomedicalValidationResult:
    if request.representation not in {"embedding", "engineered_features"}:
        raise OrchestrationError("RAW_IMAGE_NOT_SUPPORTED", "Phase 12 accepts versioned image embeddings or engineered image features, not raw high-resolution images directly in the bounded quantum circuit.", {"allowed": ["embedding", "engineered_features"]})
    if request.embedding_dim is None:
        raise OrchestrationError("EMBEDDING_DIM_REQUIRED", "Medical-image validation requires embedding_dim.", {})
    warnings = ["The image representation should be versioned and traceable to its image-generation pipeline."]
    if request.embedding_dim > 1024:
        warnings.append("Large image embeddings should be reduced before quantum encoding.")
    return BiomedicalValidationResult(modality="medical_image", valid=True, normalized={"modality": "medical_image", "samples": _samples(request.samples), "feature_count": request.embedding_dim, "representation": request.representation, "embedding_dim": request.embedding_dim, "target_column": request.target_column}, warnings=warnings)


def validate_modality(request: BiomedicalValidationRequest) -> BiomedicalValidationResult:
    if request.modality == "ehr":
        return validate_ehr(request)
    if request.modality == "genomics":
        return validate_genomics(request)
    return validate_medical_image(request)

ADAPTERS = {
    "ehr": {"label": "Electronic Health Records", "representation": "structured_tabular"},
    "genomics": {"label": "Genomics", "representation": "numeric_feature_matrix"},
    "medical_image": {"label": "Medical imaging", "representation": "embedding_or_engineered_features"},
}
