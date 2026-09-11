# Phase 7 — Held-out classical evaluation

Phase 7 evaluates frozen Phase 6 models on their untouched held-out test matrices. It records accuracy, balanced accuracy, precision, recall, F1, sensitivity, specificity, ROC-AUC when scores are available, confusion-matrix counts, class support, duration, and complete model/preprocessing/dataset lineage.

Evaluation never calls `fit`. Undefined precision, recall, F1, or specificity are reported as zero with explicit support counts. Metrics are measured from stored predictions and labels; none are fabricated.
