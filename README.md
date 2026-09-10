# EntangleX Q-Health

A modular hybrid quantum-classical machine learning platform for biomedical disease-risk prediction (SIH26139). It is a research/decision-support prototype—not a clinically validated diagnostic system.

## Current phase

Phase 2 implements real CSV/XLSX ingestion and validation: bounded uploads, safe storage names, deterministic dataset hashes, schema and quality summaries, target selection, binary class analysis, bounded previews, SQLite registration, structured API errors, and a functional React upload interface. It does not preprocess, train, predict, or fabricate metrics.

## Local setup

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
cd backend
$env:PYTHONPATH="."
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In a second PowerShell:

```powershell
cd frontend
npm install
npm test
npm run typecheck
npm run build
python -m http.server 5173 -d dist
```

Open `http://localhost:5173`; API docs are at `http://127.0.0.1:8000/docs`.

## Phase 2 workflow

Upload CSV/XLSX → validate file → parse table → inspect schema/quality → hash and register → select target → validate binary classes → preview safely.

See `docs/phase-2-report.md` for contracts, validation policy, security notes, and tests.

## Planned architecture

React UI → FastAPI API → domain services → data/ML/QML engines → evaluation/explainability/prediction → experiment registry. Quantum execution will use a simulator-first backend abstraction.

## Limitations

Phase 2 performs no imputation, scaling, encoding, feature selection, PCA, model training, explainability, or prediction. Quantum simulation is not physical quantum hardware. Future QML may perform better, similarly, or worse than classical baselines; results will not constitute clinical validation.
