# Phase 15 — Classical Explainability and Calibration

Phase 15 adds reproducible, artifact-backed explainability for persisted classical model runs.

## Outputs

- Global coefficient, tree or permutation importance
- Local perturbation explanations tied to held-out samples
- Feature-name provenance from the persisted preprocessing/model artifact
- Brier score, expected calibration error and reliability bins when probabilities are available
- Descriptive threshold tables for sensitivity, specificity, precision, F1 and false-negative rate
- Persisted explainability reports under the shared SQLite database

## Scientific boundaries

Importance is model association, not biological causation. Calibration and threshold tables describe the supplied held-out data and must not be interpreted as clinical validation. If the model does not expose probabilities, calibration and threshold analysis are reported as unavailable rather than inferred.

## API

- `POST /api/explainability/classical`
- `GET /api/explainability/reports?phase=15`
- `GET /api/explainability/reports/{report_id}`
