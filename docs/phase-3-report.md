# Phase 3 — Leakage-safe preprocessing

## Scope

Phase 3 adds configurable missing-value handling, exact-duplicate handling, categorical encoding, outlier handling, feature scaling, stratified splitting, persisted fitted pipelines, preprocessing run records, APIs, UI configuration, and tests.

## Leakage prevention

Exact duplicate removal is deterministic and occurs before splitting. The target is separated before transformations. Stratified train/test splitting occurs before any fitted operation. Outlier bounds, imputers, categorical encoders, and scalers are fitted on training data only. The held-out test set is transformed using training-fitted parameters. Outlier row removal applies only to training rows; test rows are never removed.

## Supported configuration

- Missing numerical: median or mean
- Missing categorical: most frequent
- Duplicates: keep or remove
- Categorical: one-hot or ordinal encoding
- Outliers: keep, clip, or remove using IQR or Z-score bounds
- Scaling: StandardScaler or MinMaxScaler
- Stratified test size and deterministic seed

## Persistence

Each successful run receives an ID. Configuration and summary metadata are stored in SQLite. The fitted scikit-learn pipeline, training-fitted outlier policy, label encoder, input columns, and output feature names are saved together as an internally generated joblib artifact.

## Deferred

Feature selection and PCA remain Phase 5. No model training, predictions, benchmark metrics, or quantum operations are introduced here.
