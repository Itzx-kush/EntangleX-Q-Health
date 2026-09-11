# Phase 11 — QSVM, QNN and Quantum Model Suite

## Status
Implementation complete on `phase-11-qsvm-qnn-model-suite`; merge remains blocked pending local Python 3.12/Qiskit certification and explicit owner approval.

## Implemented
- Shared `classification | regression` task contract from target validation through preprocessing, encoding, training, persistence and UI.
- Regression targets must be finite numeric values with at least three distinct outcomes.
- Regression uses deterministic non-stratified splitting, preserves floating targets, uses regression-aware ANOVA/mutual information, and rejects class-balancing methods.
- Binary classification remains the backward-compatible default.
- QSVM uses data-dependent Qiskit feature-map statevectors, a fidelity kernel `|<psi(x)|psi(z)>|^2`, and an SVC trained on the precomputed kernel.
- QNN uses an actual parameterized quantum circuit, per-qubit expectation features and a jointly optimized classical linear head.
- QNN classification uses sigmoid/binary cross-entropy and binary held-out metrics.
- QNN regression normalizes only the training target, optimizes MSE, inverse-transforms predictions and reports MAE, MSE, RMSE and R².
- VQC now supports COBYLA and Nelder–Mead, configurable tolerance, best loss, convergence state and termination metadata.
- All new runs persist configuration, seed, lineage identifiers, sample counts, circuit resources, duration, metrics and artifacts.
- Duplicate dataset uploads reuse the existing SHA-256 record.
- Phase 10 UI structure, theme behavior, responsiveness and scroll stability are preserved; Quantum Lab is extended with QSVM/QNN controls and real result panels.

## API
- `POST /api/quantum/qml/qsvm/train`
- `GET /api/quantum/qml/qsvm/{run_id}`
- `POST /api/quantum/qml/qnn/train`
- `GET /api/quantum/qml/qnn/{run_id}`
- `GET /api/quantum/qml/models?encoding_run_id=...`

## Resource bounds
- Encoded qubits: 1–8.
- QSVM training/evaluation caps: 64/256.
- QNN training/evaluation caps: 64/256.
- QNN optimizer iterations: 1–120.
- VQC optimizer iterations: 1–200.

## Validation evidence
- Python compilation passes.
- Phase 11 dependency-free contracts pass.
- Phase 9–10 encoding/scaling contracts pass.
- Frontend source/regression tests pass.
- Strict TypeScript and production build pass.
- Fixed-output and embedded-credential scans pass.
- Qiskit/scikit-learn integration tests are executable but may skip in environments missing required dependencies.

## Required local certification
Use Python 3.12 in the repository virtual environment:

```powershell
cd D:\EntangleX-Q-Health\backend
$env:PYTHONPATH = "."
& ..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Do not claim model superiority or clinical validity. Metrics are valid only for their recorded dataset split and configuration.
