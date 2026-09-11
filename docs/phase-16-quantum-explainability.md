# Phase 16 — Quantum Explainability, Stability and Uncertainty

Phase 16 adds an artifact-backed quantum audit for VQC, QSVM and QNN runs.

## Outputs

- Real feature perturbation sensitivity on encoded test features
- VQC/QNN parameter sensitivity; an explicit not-applicable state for QSVM parameters
- Circuit resource summary from the persisted run
- Seed/run stability summaries from compatible persisted quantum records
- Confidence intervals only when multiple real run records are supplied
- Explicit uncertainty and noise/hardware availability states
- Persisted quantum explainability reports under the shared SQLite database

## Scientific boundaries

The quantum audit is descriptive and does not claim causality, clinical validity or quantum advantage. Ideal-state artifacts are not relabeled as noise robustness. Noise or hardware stability remains explicitly unmeasured until real noisy-simulator or hardware records are supplied.

## API

- `POST /api/explainability/quantum`
- `GET /api/explainability/reports?phase=16`
- `GET /api/explainability/reports/{report_id}`

The frontend lets users select compatible VQC, QSVM or QNN runs; selecting multiple persisted runs enables descriptive stability intervals.
