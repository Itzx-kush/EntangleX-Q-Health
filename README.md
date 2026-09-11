# EntangleX Q-Health

A modular hybrid quantum-classical machine learning platform for biomedical disease-risk prediction (SIH26139). It is a research/decision-support prototype—not a clinically validated diagnostic system.

## Current phase

**Phase 12 — Biomedical modality adapters & training orchestration — Implemented and merged.** The platform includes leakage-safe biomedical preprocessing, classical baselines and held-out evaluation, simulator-first quantum runtime diagnostics, real quantum feature encoding, VQC, QSVM and hybrid QNN models, plus Phase 12 persistent training-job orchestration and SIH-aligned EHR, genomics and medical-imaging representation validation. Phase 12 adds a common control-plane API without replacing the certified Phase 1–11 contracts.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
$env:PYTHONPATH="."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

For the exact certified backend test environment, use Python 3.12 from the repository virtual environment:

```powershell
cd D:\EntangleX-Q-Health\backend
$env:PYTHONPATH = "."
& ..\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Frontend verification:

```powershell
cd frontend
npm install
npm test
npm run typecheck
npm run build
python -m http.server 5173 -d dist
```

Open `http://localhost:5173`; API docs are at `http://127.0.0.1:8000/docs`.

## Current workflow

Upload and validate → select classification or regression target → apply leakage-safe preprocessing and feature reduction → train classical baselines → evaluate on held-out data → run simulator-first quantum diagnostics → encode features with a real quantum circuit → train VQC, QSVM and/or QNN → orchestrate reproducible training jobs → validate biomedical modality representations → preserve dataset, preprocessing, encoding and model lineage in persisted artifacts.

See `docs/sih26139-master-roadmap.md`, `docs/sih26139-pdf-deliverable-alignment.md`, and `docs/phase-12-biomedical-orchestration.md` for the authoritative roadmap, SIH alignment, and Phase 12 implementation record.

## Planned architecture

React UI → FastAPI API → domain services → data/ML/QML engines → evaluation/explainability/prediction → experiment registry. Quantum execution remains simulator-first, with controlled near-term hardware support planned for later phases.

## Limitations

EntangleX is a research and decision-support prototype, not a clinically validated diagnostic system. Quantum simulation is not physical quantum hardware. Model metrics are valid only for their recorded dataset split and configuration. No quantum-advantage or clinical-superiority claim is made without repeatable statistical and resource evidence.
