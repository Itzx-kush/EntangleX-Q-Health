# Phase 7 — Held-out classical evaluation

Phase 7 evaluates frozen Phase 6 models on untouched held-out test matrices. It records accuracy, balanced accuracy, precision, recall, F1, sensitivity, specificity, ROC-AUC when scores are available, confusion-matrix counts, class support, duration, and full lineage.

Evaluation never calls `fit`. Undefined metrics are reported as zero with support counts. Metrics are measured, never fabricated.
