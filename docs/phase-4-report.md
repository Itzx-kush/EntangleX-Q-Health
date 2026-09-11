# Phase 4 — Training-only class-imbalance handling

## Scope

Phase 4 adds optional random oversampling, random undersampling, and SMOTE to the persisted preprocessing workflow. Resampling is deterministic, configurable, visible in the UI, and recorded with before/after class counts.

## Leakage controls

The dataset is stratified into training and test sets before any resampling. Imputers, encoders, scalers, and outlier bounds are fitted on training data only. Resampling is applied only to the transformed training matrix. Test rows and their natural class distribution are never duplicated, removed, synthesized, or used to fit SMOTE.

## Methods

- None: preserve training distribution
- Random oversampling: duplicate minority training observations
- Random undersampling: remove majority training observations
- SMOTE: synthesize minority training observations in transformed feature space

SMOTE is rejected when the minority training count is not greater than the configured neighbor count.

## Recorded metadata

- Training rows before and after resampling
- Rows added or removed
- Training class distribution before and after
- Untouched test class distribution
- Method and deterministic seed

## Deferred

Feature selection and PCA remain Phase 5. Phase 4 does not train models, calculate performance metrics, or claim that balancing improves clinical performance.
