# EntangleX Q-Health

A modular hybrid quantum-classical machine learning platform for biomedical disease-risk prediction (SIH26139). It is a research/decision-support prototype—not a clinically validated diagnostic system.

## Current phase

**Phase 18 of 20 — Prediction, decision support and evidence cockpit — implemented for the certified Phase 1–16 baseline.** Phase 17 adds persisted artifact-backed prediction, held-out sample selection, configurable descriptive risk bands and explicit uncertainty boundaries. Phase 18 adds an animated EntangleX launch sequence, quantum-inspired visual system, theme-aware logo assets, live evidence cockpit, JSON evidence export and a complete local settings center. Missing measurements are never fabricated and no clinical or quantum-advantage claim is implied.

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

Upload and validate → select classification or regression target → apply leakage-safe preprocessing and feature reduction → train classical baselines → evaluate on held-out data → run simulator-first quantum diagnostics → encode features with a real quantum circuit → train VQC, QSVM and/or QNN → orchestrate reproducible training jobs → register immutable evidence → benchmark real repeated validation folds → generate classical explanations and calibration evidence → generate quantum audit and stability evidence → generate an artifact-backed prediction → review the Phase 18 evidence cockpit and export a live summary.

See `docs/sih26139-master-roadmap.md`, `docs/sih26139-pdf-deliverable-alignment.md`, `docs/phase-12-biomedical-orchestration.md`, `docs/phase-13-experiment-registry.md`, `docs/phase-14-rigorous-benchmarking.md`, `docs/phase-15-classical-explainability.md`, `docs/phase-16-quantum-explainability.md`, `docs/phase-17-prediction-decision-support.md`, and `docs/phase-18-product-experience.md`.

## Product experience

The frontend now opens with a short quantum-transition EntangleX logo animation, preserves the black wordmark in light mode and uses a white wordmark in dark mode. The toolbar exposes Theme, Settings, Help and Decision Center. Settings are browser-local and organized into Appearance, General, Experiments & ML, Quantum, Benchmarking, Privacy & Security, Notifications, Data & Storage, Explainability, Prediction, Advanced and About.

## Limitations

EntangleX is a research and decision-support prototype, not a clinically validated diagnostic system. Quantum simulation is not physical quantum hardware. Model metrics are valid only for their recorded dataset split and configuration. Model explanations describe learned associations, not biological causation. Risk bands are configurable descriptive thresholds, not validated clinical categories. A single prediction does not provide uncertainty. Noise and hardware robustness are reported only when real noisy-simulator or hardware records exist. No quantum-advantage or clinical-superiority claim is made without repeatable statistical and resource evidence.
