# EntangleX Q-Health

A modular hybrid quantum-classical machine learning platform for biomedical disease-risk prediction (SIH26139). It is a research/decision-support prototype—not a clinically validated diagnostic system.

## Current phase

**Phase 13 — Experiment Registry and Reproducibility — implemented on the draft development branch.** Phase 13 adds immutable experiment lineage, environment/package capture, seed and nondeterminism records, SHA-256 artifact manifests, integrity validation, cloning, compatible descriptive comparison, dataset/model cards, and JSON/ZIP evidence export.

**Phase 14 — Rigorous Classical-vs-Quantum Benchmarking — implemented on the same draft development branch.** Phase 14 aggregates user-supplied repeated stratified fold records with confidence intervals, calibration metrics, generalization gaps, training/inference/simulator and circuit-resource accounting, and honest better/comparable/worse/inconclusive conclusions. It never fabricates missing metrics or asserts clinical or quantum advantage.

## Local setup

```powershell
python -m venv .venv
.venv\\Scripts\\Activate.ps1
python -m pip install -r backend\\requirements.txt
cd backend
$env:PYTHONPATH="."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Backend validation

```powershell
Set-Location D:\\EntangleX-Q-Health\\backend
$env:PYTHONPATH = "."
& ..\\.venv\\Scripts\\python.exe -m pytest -q
```

## Frontend validation

```powershell
Set-Location D:\\EntangleX-Q-Health\\frontend
npm install
npm test
npm run typecheck
npm run build
python -m http.server 5173 -d dist
```

Open `http://localhost:5173`; API docs are at `http://127.0.0.1:8000/docs`.

## Current workflow

Upload and validate → select classification or regression target → apply leakage-safe preprocessing and feature reduction → train classical baselines → evaluate on held-out data → run simulator-first quantum diagnostics → encode features with a real quantum circuit → train VQC, QSVM and/or QNN → orchestrate reproducible training jobs → register immutable evidence → benchmark real repeated validation folds and resource measurements.

See `docs/sih26139-master-roadmap.md`, `docs/sih26139-pdf-deliverable-alignment.md`, `docs/phase-12-biomedical-orchestration.md`, `docs/phase-13-experiment-registry.md`, and `docs/phase-14-rigorous-benchmarking.md` for the roadmap and implementation records.

## Limitations

EntangleX is a research and decision-support prototype, not a clinically validated diagnostic system. Quantum simulation is not physical quantum hardware. Model metrics are valid only for their recorded dataset split and configuration. No quantum-advantage or clinical-superiority claim is made without repeatable statistical and resource evidence.
