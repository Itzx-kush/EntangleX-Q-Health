# Phase 2 — Dataset ingestion and validation

## Scope

Phase 2 adds CSV/XLSX ingestion, bounded multipart reading, extension/size/content validation, dataframe parsing, schema profiling, deterministic SHA-256 hashes, duplicate-upload prevention, safe generated filenames, SQLite dataset metadata, target selection, binary-target validation, class-balance analysis, bounded previews, structured errors, API routes, and a real upload UI.

## API

- `POST /api/datasets/upload` — multipart file; optional `target_column` form field.
- `GET /api/datasets` — registered datasets.
- `GET /api/datasets/{dataset_id}` — one dataset summary.
- `POST /api/datasets/{dataset_id}/target` — validate and select binary target.
- `POST /api/datasets/{dataset_id}/preview` — bounded preview (1–100 rows).

## Validation policy

Serious problems are rejected: empty files/datasets, unsupported extensions, oversized files, parse failures, empty/duplicate column names, unsupported scalar types, infinite numeric values, missing target values, absent targets, and non-binary targets. Missing feature values, duplicate rows, and high class imbalance are reported without silent repair.

## Security and privacy

Original filenames are never used as storage paths. Files receive UUID names, uploads are read with a hard byte limit, uploaded content is never executed, hashes support provenance, and only bounded previews are returned. No patient-identifiable demo data is included.

## Test plan

- CSV and XLSX parsing
- schema/type profiling
- missing-value and duplicate reporting
- deterministic hash presence and duplicate prevention
- file extension/empty-file rejection
- binary/single-class target validation
- bounded preview and JSON-safe values
- upload/list/target/preview API flow
- structured validation errors
- frontend typecheck/build/source contract tests

## Deferred to Phase 3

No imputation, encoding, scaling, outlier changes, feature selection, PCA, SMOTE, or train/test transformation occurs in Phase 2.
