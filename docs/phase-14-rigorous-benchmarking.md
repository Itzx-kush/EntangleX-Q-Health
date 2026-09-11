# Phase 14 — Rigorous Classical-vs-Quantum Benchmarking

## Delivered

- Persistent benchmark reports under `/api/benchmarks`.
- Repeated stratified validation plans that require at least two supplied fold records per selected experiment.
- Fold-level validation metrics or computation from supplied labels/predictions.
- Accuracy, sensitivity, specificity, precision, F1, Brier score, and expected calibration error when the necessary real inputs are supplied.
- Mean, sample standard deviation, and 95% normal-approximation intervals; one-fold intervals remain unavailable rather than fabricated.
- Generalization gaps from paired train and validation metrics.
- Training/inference/simulator time, duration, circuit depth/size, memory, and shot accounting when supplied.
- Descriptive better/comparable/worse/inconclusive conclusions based on interval separation, explicitly not a superiority claim.
- Frontend benchmarking workspace with explicit experiment selection and JSON fold-record input.

## Input contract

The frontend and API accept a mapping from experiment IDs to real fold records. Each record may include `validation_metrics`, `train_metrics`, `labels`, `predictions`, `probabilities`, `duration_seconds`, and `resource_measurements`. Missing measurements remain missing. No synthetic example is submitted by the UI.

## Scientific boundary

The report is descriptive research evidence. It does not establish clinical validity, causal superiority, or quantum advantage. Comparisons require compatible task type, model family, and modality.
