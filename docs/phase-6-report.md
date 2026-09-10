# Phase 6 — Classical baseline training

Phase 6 trains reproducible Logistic Regression, SVM, and Random Forest baselines from persisted Phase 5 training matrices. Configuration, seed, training rows, feature count, class distribution, duration, preprocessing lineage, and artifact reference are stored. Held-out test data is packaged for Phase 7 evaluation but never used during fitting.

No performance metric is calculated in Phase 6. Measured evaluation begins in Phase 7.
