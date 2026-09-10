# EntangleX Q-Health — Engineering Assessment and Phase 1 Plan

## A. Architecture summary

EntangleX Q-Health will be a modular monorepo with a React/TypeScript delivery layer and a FastAPI service boundary. The backend will be organized around application services and typed contracts rather than route-owned business logic. Dataset, preprocessing, feature engineering, classical ML, quantum ML, evaluation, explainability, prediction, and experiment-registry modules will remain independently testable.

The benchmark engine will consume model adapters through a common interface and will enforce a shared dataset version, target, split, preprocessing configuration, feature set, and evaluation protocol. Experiment records will capture configuration, software versions, timings, artifacts, and measured metrics. Quantum execution will sit behind a backend abstraction; local simulation is the default, with real hardware support optional and non-blocking.

Phase 1 intentionally creates only the repository foundation, configuration, backend/frontend shells, database connectivity check, quantum capability probe, health endpoint, tests, and local/container launch contracts. It does not fabricate later-phase functionality.

## B. Repository structure

```text
entanglex-q-health/
├── backend/
│   ├── app/
│   │   ├── api/                 # versioned route modules
│   │   ├── core/                # settings, logging, errors
│   │   ├── services/            # health and future use-case services
│   │   ├── storage/             # database/session abstractions
│   │   ├── main.py
│   │   └── version.py
│   ├── tests/
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── services/
│   │   ├── styles/
│   │   └── types/
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── Dockerfile
├── data/                         # ignored runtime datasets
├── experiments/                  # ignored experiment artifacts
├── models/                       # ignored model artifacts
├── docs/
├── .env.example
├── docker-compose.yml
├── Makefile
└── README.md
```

Later phases will add domain packages for data ingestion, preprocessing, feature engineering, model adapters, quantum circuits/backends, evaluation, explainability, predictions, and registries without turning `main.py` into a monolith.

## C. Dependency compatibility assessment

### Inspected environment

- OS: Amazon Linux 2023.12 (x86_64), kernel 6.18
- Python: 3.13.14
- Node.js: 24.14.1
- npm: 11.11.0
- GCC/G++: 11.5.0; GNU Make 4.3; Git 2.49.0
- CMake, Docker, and Podman are not installed in the sandbox
- React 19.2.8 and TypeScript 7.0.2 are preinstalled globally in the sandbox module set
- FastAPI, Uvicorn, SQLAlchemy, pytest, scikit-learn, SciPy, Qiskit, Qiskit Machine Learning, Qiskit Aer, XGBoost, and SHAP were not initially installed

### Assessment

1. Phase 1 can target Python 3.13 after installing and verifying FastAPI, Pydantic, Uvicorn, SQLAlchemy, pytest, and HTTPX in an isolated virtual environment.
2. Quantum packages must not be pinned yet. Python 3.13 wheel/API support can differ across Qiskit components. Before Phase 6/7, create an isolated compatibility probe that installs candidate versions and verifies imports for primitives, Aer, VQC, QSVC, feature maps, ansatz classes, optimizers, and a tiny training run.
3. React 19 is acceptable for the shell. Vite and testing packages must be installed and verified locally before their exact versions are pinned.
4. Docker files can be authored, but container execution cannot be certified in this sandbox because no container runtime is installed. Local execution remains the Phase 1 acceptance gate.
5. The production container should use a Qiskit-supported Python version (preferably 3.12 unless Phase 6 proves full 3.13 compatibility) so the host runtime does not force risky quantum dependency choices.

## D. Phase 1 implementation plan

1. Create monorepo directories and ignore rules.
2. Create centralized backend settings and structured logging.
3. Add SQLite connectivity abstraction without domain tables yet.
4. Add runtime capability probes for Python and optional quantum packages.
5. Implement `GET /health` with application version, database state, and quantum simulator availability.
6. Add a structured API error envelope and CORS configuration.
7. Create React/TypeScript/Vite application shell with first-run choices, architecture summary, health indicator, research disclaimer, and no fake metrics.
8. Add backend unit/API tests and frontend component/build checks.
9. Add local run instructions, environment template, Dockerfiles, Compose contract, Makefile, and CI-ready commands.
10. Start backend, call the real health endpoint, build the frontend, run tests, and fix failures before ending Phase 1.

## E. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Qiskit component/API mismatch | Isolated compatibility matrix and executable import/training probes before quantum implementation; pin only tested versions. |
| Python 3.13 quantum wheel gaps | Prefer Python 3.12 in containers if full stack verification fails on 3.13. |
| Data leakage | Build preprocessing as train-fitted pipelines; later tests will assert fold isolation. |
| Invalid quantum-advantage claims | Benchmark engine reports measured outcomes and rule-based observations only; no seeded UI metrics. |
| Long-running training blocks API | Job abstraction with status/progress in the service layer; future worker adapter. |
| Sensitive biomedical uploads | Size/type validation, safe filenames, minimal retention/logging, no execution of uploads. |
| Unfair comparisons | Immutable shared benchmark context: dataset hash, split, pipeline, target, seed, and test set. |
| Quantum simulation cost | Configurable limits for rows, qubits, depth, folds, and search spaces; simulator-first defaults. |
| Docker unavailable in current sandbox | Validate Docker syntax/configuration where possible and make local startup the executable gate; certify Compose later in a runtime-enabled environment. |
| Frontend becoming a decorative mock | Phase 1 shows only platform state and navigation; every later chart/metric must bind to API results. |

## Phase 1 acceptance gate

- Backend imports and starts.
- `GET /health` returns structured live status.
- SQLite connectivity probe succeeds.
- Missing Qiskit is reported as unavailable, not as a crash.
- Backend tests pass.
- Frontend type-checks and builds.
- Frontend tests pass.
- Frontend reads the backend health endpoint.
- No fake metrics, predictions, circuits, or claims exist.
- Local setup and container contracts are documented.
