# Phase 6 — Classical baseline training

Phase 6 trains reproducible Logistic Regression, SVM, and Random Forest baselines from persisted Phase 5 training matrices. Model configuration, seed, training rows, feature count, class distribution, duration, preprocessing lineage, and artifact reference are stored. The held-out test matrix is packaged for Phase 7 evaluation but never used during model fitting.

No accuracy, AUC, sensitivity, specificity, or other performance metric is calculated in Phase 6. Measured evaluation begins in Phase 7.
