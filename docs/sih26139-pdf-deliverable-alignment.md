# SIH26139 PDF Deliverable Alignment

The attached two-page SIH26139 document confirms the platform requirements and provides five explicit deliverables.

| PDF deliverable | Exact capability expected | EntangleX phase coverage |
|---|---|---|
| Data Pre-processing & Feature Engineering Module | Cleaning, normalization, dimensionality reduction, feature selection, missing/noisy-data handling | Phases 2–5; biomedical adapters in Phase 12 |
| Hybrid Quantum-Classical Architecture | Classical frontend, QPU/simulator, data encoding | Phases 1, 8–12; hardware hardening in Phase 19 |
| Quantum Machine Learning Models | VQC, Quantum SVM, QNN or equivalent parameterized circuits | VQC in Phases 9–10; QSVM/QNN in Phase 11 |
| Prediction & Decision Support Module | Disease probability scores, early-risk stratification, threshold tuning for sensitivity/specificity | Benchmark/calibration in Phase 14; explainability in 15–16; inference and decision support in Phase 17 |
| Software Platform / Prototype | UI/API, dataset upload, model training/evaluation dashboard, result visualization | Foundation through Phase 10; complete dashboard/reporting in Phase 18; final delivery in Phase 20 |

## Required roadmap corrections after reviewing the PDF

1. Phase 11 must add at least a quantum-kernel/QSVM and a QNN/hybrid model; VQC alone is only partial coverage.
2. Phase 11 should introduce classification/regression task abstraction and a bounded regression path for suitable biomedical targets.
3. Phase 12 should add genomics feature matrices and medical-image embedding adapters while preserving training-only fitting and lineage.
4. Phase 14 must include calibration, repeated validation, confidence intervals, computational-resource evidence and generalization analysis.
5. Phase 17 is explicitly a **Prediction & Decision Support** phase: single/batch inference, disease probabilities, early-risk bands and sensitivity/specificity threshold tuning.
6. Phase 18 must visualize real probability, risk, threshold, benchmark, explanation and circuit-resource results.
7. “Improve accuracy” is an objective to test, not a claim to hardcode. Reports must allow better, comparable, worse and inconclusive outcomes.

## Current readiness

- Phases 1–8: certified.
- Phases 9–10: implemented on draft PR #8; local Python 3.12/Qiskit certification pending.
- Delivery 1 is substantially implemented for tabular biomedical data.
- Delivery 2 has a working simulator-first architecture and real data encoding.
- Delivery 3 currently includes VQC; QSVM/QNN are planned next.
- Delivery 4 is not complete until Phase 17.
- Delivery 5 is partially complete and will be finalized in Phase 18 and Phase 20.

## UI preservation rule

The Phase 10 interface remains the protected baseline. Future work must extend—not replace—the Dashboard, ML Pipeline, Quantum Lab and Evidence structure, persistent themes, responsive layout, contrast, scroll stability, backend-driven metrics and scientific safeguards.