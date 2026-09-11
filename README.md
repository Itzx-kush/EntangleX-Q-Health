# EntangleX Q-Health

A modular hybrid quantum-classical machine learning platform for biomedical disease-risk prediction (SIH26139). It is a research/decision-support prototype—not a clinically validated diagnostic system.

## Current phase

Phase 3 adds leakage-safe configurable preprocessing: stratified splitting, train-only fitted imputation, categorical encoding, outlier bounds, scaling, duplicate handling, persisted pipeline artifacts, run metadata, APIs, and a functional configuration interface. It does not perform feature selection, PCA, model training, prediction, or fabricate metrics.

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

## Phase 3 workflow

Upload and validate → select binary target → remove exact duplicates if configured → stratified split → fit outlier policy and scikit-learn transformations on training data only → transform held-out test → persist the fitted bundle and run metadata.

See `docs/phase-3-report.md` for leakage controls and supported configuration.

## Planned architecture

React UI → FastAPI API → domain services → data/ML/QML engines → evaluation/explainability/prediction → experiment registry. Quantum execution will use a simulator-first backend abstraction.

## Limitations

Phase 2 performs no imputation, scaling, encoding, feature selection, PCA, model training, explainability, or prediction. Quantum simulation is not physical quantum hardware. Future QML may perform better, similarly, or worse than classical baselines; results will not constitute clinical validation.
