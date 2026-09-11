# Phase 17 — Prediction and Decision Support

Phase 17 adds production-shaped prediction flows while preserving the research-only boundary.

## Delivered

- Single-record prediction from a persisted classical model artifact
- Recorded held-out sample selection for reproducible demonstrations
- Optional explicit feature-vector input with artifact feature-count validation
- Probability output when the estimator genuinely exposes probabilities
- Configurable probability threshold and low/intermediate/high descriptive bands
- Persisted prediction records that store an input hash, not raw biomedical records
- Prediction history and a decision-center UI
- Explicit unavailable probability and single-record uncertainty states

## Scientific boundary

Risk bands are configurable descriptive thresholds, not validated clinical categories. A prediction is not a diagnosis. Uncertainty is not inferred from one record. No input is silently fabricated when the user has not selected a held-out sample or supplied a feature vector.

## API

- `POST /api/predictions`
- `GET /api/predictions`
- `GET /api/predictions/{prediction_id}`
