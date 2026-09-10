# EntangleX Q-Health

A modular hybrid quantum-classical machine learning platform for biomedical disease-risk prediction (SIH26139). It is a research/decision-support prototype—not a clinically validated diagnostic system.

## Phase status

Phase 1 establishes the monorepo, configuration, FastAPI application contract, SQLite health probe, structured logging, React/TypeScript shell, tests, and local/container launch files. Dataset, ML, QML, benchmarking, explainability, and prediction functionality will be added only in their validated phases. No metrics or model outputs are mocked.

## Architecture

React UI → FastAPI API → domain services → data/ML/QML engines → evaluation/explainability/prediction → experiment registry. Quantum execution will use a simulator-first backend abstraction.

See `docs/phase-1-engineering-assessment.md`.

## Local backend

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r backend/requirements.txt
cd backend
uvicorn app.main:app --reload --port 8000
```

Open `http://localhost:8000/health` or `/docs`.

If dependencies cannot be installed, `python backend/dev_server.py` runs a dependency-free validation harness for the same health service; it is not the production backend.

## Local frontend

```bash
cd frontend
npm install
npm run build
npm run dev
```

## Docker

```bash
cp .env.example .env
docker compose up --build
```

The current sandbox has no Docker runtime, so Compose execution must be certified in a Docker-enabled environment.

## Testing

```bash
make test
```

## Planned training workflow

Upload → validate → stratified split → train-fitted preprocessing → feature selection → PCA → classical baselines + VQC → unified benchmark → explainability → prediction → immutable experiment record.

## Planned models

Classical: Logistic Regression, SVM, Random Forest; optional XGBoost. Quantum: VQC first, QSVC second, QNN only after MVP stability. Quantum APIs and versions will be pinned only after executable compatibility probes.

## Evaluation and explainability

Measured accuracy, precision, recall/sensitivity, specificity, F1, ROC-AUC, train/inference time, confusion matrices, CV variation and generalization checks. Classical explanations use SHAP/permutation importance where supported; quantum models use clearly labeled feature perturbation/sensitivity analysis.

## Limitations

Quantum simulation is not physical quantum hardware. QML may be better, similar, or worse than classical baselines. Results depend on data and protocol and do not constitute clinical validation.
