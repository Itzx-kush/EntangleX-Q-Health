# Phase 5 — Training-only feature selection and PCA

Phase 5 adds variance filtering, ANOVA selection, mutual-information selection, and optional PCA. Every selector and reducer is fitted only on transformed training data. The held-out test matrix is transformed with those fitted objects. Resampling then operates on the reduced training matrix only.

## Recorded evidence

- Transformed feature count
- Selected feature count and names
- Final output dimension
- PCA component names
- Measured explained-variance ratios and total
- Deterministic seed and full configuration

Invalid feature counts, empty selections, and excessive PCA dimensions return structured errors. No explained variance or performance value is fabricated. Model training remains Phase 6.
