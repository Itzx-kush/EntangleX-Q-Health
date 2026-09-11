# EntangleX Q-Health — SIH26139 Master Roadmap

## Authoritative problem target

**Problem ID:** 26139  
**Title:** Hybrid Quantum Machine Learning Platform for Early Disease Detection  
**Organization:** Egreen Quanta  
**Category:** Software  
**Theme:** MedTech / BioTech / HealthTech

The required product is a functional research platform—not a static demonstration—that accepts biomedical data, performs leakage-safe classical preparation, trains classical and quantum-enhanced models, supports prediction and explainability, and benchmarks both tracks for predictive performance, computational efficiency, and generalization. It must remain executable on simulators while providing a controlled route to near-term hardware.

## Delivery status through Phase 11

| Phase | Scope | Delivered outcome | Status |
|---|---|---|---|
| 1 | Engineering foundation | React/TypeScript frontend, FastAPI backend, configuration, health endpoints, SQLite foundation, scientific-claim boundaries | Certified |
| 2 | Biomedical data ingestion | CSV/XLSX upload, validation, SHA-256 deduplication, schema profiling, target selection, preview, metadata persistence | Certified |
| 3 | Leakage-safe preprocessing | Stratified train/test split; train-only imputation, encoding and scaling; duplicate/outlier handling; persisted artifacts | Certified |
| 4 | Class imbalance | None, random over/under-sampling and SMOTE applied only to training data with deterministic metadata | Certified |
| 5 | Feature engineering | Variance, ANOVA and mutual-information selection plus PCA, fitted on training data only | Certified |
| 6 | Classical baselines | Logistic Regression, SVM and Random Forest with real configuration, training and model artifacts | Certified |
| 7 | Classical evaluation | Untouched-test metrics, confusion matrix, sensitivity, specificity, balanced accuracy, F1 and ROC-AUC | Certified |
| 8 | Quantum runtime and product UI | Simulator-first Qiskit Aer diagnostics, GHZ health circuit, bounded resources, optional IBM capability, persisted runs, initial complete website | Certified |
| 9 | Quantum feature encoding | Real preprocessing-artifact input, train-only [0, π] angle scaling, Qiskit RY gates, linear/ring entanglement, circuit resources and NPZ artifacts | Certified |
| 10 | Variational quantum classifier | Statevector VQC, repeated RY ansatz, COBYLA/binary-cross-entropy optimization, held-out evaluation, real loss/metrics/artifacts and polished stable UI | Certified |
| 11 | Quantum model suite | Bounded QSVM/fidelity-kernel model, QNN/hybrid neural model, hardened VQC configuration, classification/regression task abstractions, preserved lineage and Phase 11 contract tests | Certified |

## Phase 11 certification evidence

Phase 11 was merged into `main` as pull request #9 at commit `6d34595`. Local certification was then completed on Windows using the repository Python 3.12 virtual environment. The full backend suite passed:

```text
Ran 43 tests in 1.729s

OK
```

This certification covers the complete discovered backend test suite, including the Phase 11 QSVM/QNN contract and quantum execution tests. Warnings emitted by third-party dependencies did not cause test failures.

## Fit against SIH26139

### Strongly covered now

- End-to-end tabular biomedical data ingestion and validation
- Leakage-safe preprocessing and feature reduction for high-dimensional data
- Multiple classical baselines
- Real quantum circuit encoding, VQC, QSVM and QNN/hybrid modeling
- Simulator-first execution with deterministic seeds and resource bounds
- Classification and bounded regression task abstractions
- Accuracy, balanced accuracy, precision, recall, F1, sensitivity, specificity and ROC-AUC where applicable
- Persisted data/model/QML lineage and reproducibility metadata
- Professional frontend with real-state outputs and no fabricated metrics

### Still incomplete or only partially covered

1. **Biomedical modality breadth:** tabular CSV/XLSX is complete, but genomics and image workflows require feature/embedding adapters rather than sending raw high-dimensional input to a quantum circuit.
2. **Inference workflow:** trained models require single-record and batch prediction, validation, confidence/uncertainty and saved inference records.
3. **Explainability:** classical and quantum explanation modules have not yet been implemented.
4. **Benchmark rigor:** single-run metrics are insufficient. Add repeated stratified validation, confidence intervals, generalization checks and measured runtime/resource comparisons.
5. **Hardware compatibility:** runtime capability exists, but controlled real-device transpilation, queues, calibration metadata, noise experiments and execution safeguards remain.
6. **Scalability and privacy:** add async jobs, artifact lifecycle, access controls, audit logs, PHI-safe defaults and deployment hardening.
7. **Comprehensive delivery documentation:** architecture, user guide, API guide, model cards, dataset cards, deployment, limitations and SIH demonstration package remain.

**Important scientific correction:** “Improve accuracy, sensitivity and specificity” is an evaluation objective, not a result that may be promised. EntangleX must measure whether a quantum/hybrid model improves those metrics under controlled experiments and report negative or neutral results honestly. No quantum-advantage claim is allowed without repeatable statistical and resource evidence.

## Revised future roadmap

### Phase 12 — Biomedical modality adapters and training orchestration

- Orchestrate classical, VQC, QSVM and QNN jobs through a common run contract.
- Add tabular EHR adapter metadata, genomics feature-matrix support and image-embedding ingestion.
- Never send raw medical images directly to small quantum circuits; use versioned classical embeddings or medically appropriate engineered features.
- Add bounded job states, cancellation, progress, failure recovery and deterministic reruns.

**Exit gate:** a user can launch and monitor valid hybrid experiments across supported biomedical feature formats.

### Phase 13 — Experiment registry and reproducibility

- Central experiment registry linking dataset, split, preprocessing, feature reduction, model, environment and metrics.
- Configuration snapshots, package versions, artifact checksums and random seeds.
- Run comparison, cloning, export/import and immutable evidence records.
- Dataset cards and model cards with limitations and intended use.

**Exit gate:** an independent evaluator can reconstruct a run from recorded evidence.

### Phase 14 — Rigorous classical-versus-quantum benchmarking

- Repeated stratified cross-validation or repeated holdout under identical data conditions.
- Accuracy, sensitivity, specificity, F1, balanced accuracy, ROC-AUC and calibration.
- Training/inference time, simulator time, circuit depth, parameter count, memory and shot/resource costs.
- Confidence intervals, variance, generalization-gap analysis and statistical comparisons.
- Honest conclusion states: better, comparable, worse or inconclusive.

**Exit gate:** benchmark reports contain measured evidence rather than promotional claims.

### Phase 15 — Classical explainability and clinical interpretation aids

- Global and local feature importance.
- Model-appropriate SHAP/permutation/coefficient/tree explanations.
- Feature provenance back to original biomedical columns.
- Calibration curves, threshold selection and false-negative/false-positive analysis.
- Research disclaimers and non-diagnostic presentation.

**Exit gate:** each supported classical prediction can be explained and traced safely.

### Phase 16 — Quantum explainability, uncertainty and sensitivity

- Parameter/feature sensitivity and ablation studies.
- Quantum-kernel similarity views and circuit contribution summaries where technically defensible.
- Prediction uncertainty, stability across seeds and noise sensitivity.
- Clear separation of measured explanation from speculative quantum interpretation.

**Exit gate:** QML behavior can be inspected without fabricated causal explanations.

### Phase 17 — Inference API and prediction workflows

- Single-record and batch inference with schema validation.
- Reuse frozen preprocessing, feature reduction, encoding and model artifacts exactly.
- Threshold controls, confidence/uncertainty, explanation links and inference history.
- Versioned API contracts and safe error responses.

**Exit gate:** certified models can perform traceable end-to-end predictions on valid new data.

### Phase 18 — Complete dashboard and reporting

- Preserve the current visual system while extending Dashboard, ML Pipeline, Quantum Lab and Evidence.
- Experiment browser, benchmark comparison, explainability views, inference workspace and exportable reports.
- Responsive desktop/tablet/mobile behavior, accessibility and keyboard validation.
- Real progress and empty states only; never placeholder performance numbers.

**Exit gate:** every backend capability is available through a coherent, professional interface.

### Phase 19 — Scalability, security, privacy and near-term hardware

- Async/background execution, workload limits, caching and artifact retention.
- PHI-safe defaults, upload controls, audit logging, dependency/security scanning and deployment hardening.
- Environment-only secrets and role-aware access controls.
- Optional IBM hardware execution with explicit confirmation, transpilation evidence, calibration/noise metadata and cost/queue safeguards.
- Containerized deployment, observability, backup and recovery documentation.

**Exit gate:** the platform is safely deployable and simulator-first while remaining hardware-compatible.

### Phase 20 — SIH validation and final delivery

- Full regression, security, performance, usability and reproducibility testing.
- Validate real/benchmark cancer, cardiovascular or neurological datasets where licensing permits.
- Architecture document, setup guide, user guide, API guide, dataset/model cards and scientific limitations.
- Demonstration script, screenshots, pitch evidence, deployment package and final delivery matrix.
- Record all unresolved limitations and future research honestly.

**Exit gate:** a fresh evaluator can install, operate, reproduce and assess the complete platform.

## UI preservation contract (effective from Phase 10)

The current Phase 10 interface is the protected product baseline.

### Protected structure

- Persistent left navigation with Dashboard, ML Pipeline, Quantum Lab and Evidence.
- Sticky application header, API-status indicator and theme switch.
- Dashboard hero, real-state KPI cards, nine-stage workflow and classical/quantum track cards.
- ML Pipeline sequence: dataset/target → preprocessing → baseline training → held-out evaluation.
- Quantum Lab separation: Phase 8 runtime diagnostic versus dataset-dependent encoding/VQC.
- Evidence lineage and scientific-boundary presentation.

### Protected behavior

- No component-definition pattern that causes workspaces to remount after state changes.
- No click or Enter-key scroll jump.
- All actions use explicit button types and remain keyboard accessible.
- Theme persists through `entanglex-theme` local storage.
- Classical-model text remains readable in light and dark themes.
- Responsive desktop, tablet and mobile layouts remain functional.
- Hover, focus-visible, loading, error, success and empty states are retained.
- Dashboard and metric views use backend state only; no demonstration metrics.

### Change policy

Future phases may add cards, tabs, charts and workspaces using the existing tokens and components. They must not replace the visual identity, navigation model, theme behavior or scientific safeguards unless the project owner explicitly approves a redesign. Every phase must run UI regression tests for navigation labels, contrast, theme persistence, responsive overflow, keyboard behavior, scroll stability, API wiring and absence of fabricated results.

## Expected delivery table

| SIH expected deliverable | Responsible phases |
|---|---|
| Hybrid quantum-classical architecture | 1, 8–12 |
| Biomedical data handling pipeline | 2–5, 12 |
| Classical baselines | 6–7 |
| Quantum-enhanced models | 9–11 |
| Hybrid training workflow | 10–13 |
| Prediction/inference | 17 |
| Performance and generalization evaluation | 7, 14 |
| Computational-efficiency benchmark | 8–14 |
| Classical and quantum explainability | 15–16 |
| Simulator and near-term hardware compatibility | 8, 19 |
| Scalable, secure software platform | 12, 19 |
| Complete professional dashboard | 8, 10, 18 |
| Comprehensive documentation and SIH package | 13, 20 |

## Merge and certification policy

Phase 11 is now merged and locally certified on Python 3.12/Qiskit. Future phases must branch from the latest explicitly certified merge. No phase may be merged solely because static tests pass when its core runtime dependency was unavailable.
