# EntangleX Q-Health

A modular hybrid quantum-classical machine learning platform for biomedical disease-risk prediction (SIH26139). It is a research/decision-support prototype—not a clinically validated diagnostic system.

## Current phase

**Phase 16 of 20 — Explainability, calibration, quantum audit and uncertainty — implemented for the certified Phase 1–14 baseline.** Phase 15 adds artifact-backed global and local classical explanations, feature provenance, calibration evidence and sensitivity/specificity threshold tables. Phase 16 adds real quantum feature and parameter perturbation, circuit-resource summaries, compatible-run stability analysis and explicit noise/hardware evidence states. Missing measurements are never fabricated and no clinical or quantum-advantage claim is implied.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
$env:PYTHONPATH="."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Backend validation

```powershell
Set-Location D:\EntangleX-Q-Health\backend
$env:PYTHONPATH = "."
& ..\.venv\Scripts\python.exe -m pytest -q
```

## Frontend validation

```powershell
Set-Location D:\EntangleX-Q-Health\frontend
npm install
npm test
npm run typecheck
npm run build
python -m http.server 5173 -d dist
```

Open `http://localhost:5173`; API docs are at `http://127.0.0.1:8000/docs`.

## Current workflow

Upload and validate → select classification or regression target → apply leakage-safe preprocessing and feature reduction → train classical baselines → evaluate on held-out data → run simulator-first quantum diagnostics → encode features with a real quantum circuit → train VQC, QSVM and/or QNN → orchestrate reproducible training jobs → register immutable evidence → benchmark real repeated validation folds → generate classical explanations and calibration evidence → generate quantum audit and stability evidence.

See `docs/sih26139-master-roadmap.md`, `docs/sih26139-pdf-deliverable-alignment.md`, `docs/phase-12-biomedical-orchestration.md`, `docs/phase-13-experiment-registry.md`, `docs/phase-14-rigorous-benchmarking.md`, `docs/phase-15-classical-explainability.md`, and `docs/phase-16-quantum-explainability.md`.

## Limitations

EntangleX is a research and decision-support prototype, not a clinically validated diagnostic system. Quantum simulation is not physical quantum hardware. Model metrics are valid only for their recorded dataset split and configuration. Model explanations describe learned associations, not biological causation. Noise and hardware robustness are reported only when real noisy-simulator or hardware records exist. No quantum-advantage or clinical-superiority claim is made without repeatable statistical and resource evidence.
