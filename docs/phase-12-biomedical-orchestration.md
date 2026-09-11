# Phase 12 — Biomedical Modality Adapters & Training Orchestration

## Scope

Phase 12 extends the certified Phase 1–11 platform without replacing existing contracts. It adds a common orchestration boundary for classical and quantum training plus explicit adapters for the three biomedical data families named by SIH26139: electronic health records, genomics, and medical imaging.

## Implemented

- `backend/app/orchestration/` — persistent training-job schema, repository, service, and API contracts.
- `backend/app/biomedical/adapters.py` — EHR, genomics, and medical-image validation/normalization adapters.
- `POST /api/orchestration/validate` — modality contract validation.
- `GET /api/orchestration/capabilities` — machine-readable modality/model capabilities.
- `POST /api/orchestration/jobs` — create a reproducible queued training job.
- `POST /api/orchestration/jobs/{id}/run` — execute the selected existing classical/QML service through one orchestration boundary.
- `POST /api/orchestration/jobs/{id}/cancel` — persistent cancellation request/state for queued jobs.
- `POST /api/orchestration/jobs/{id}/rerun` — create a new job linked to the original through `parent_job_id`.
- `GET /api/orchestration/jobs` and `GET /api/orchestration/jobs/{id}` — job history and status.
- Frontend TypeScript contracts and API client functions for Phase 12 orchestration.
- Dedicated Phase 12 backend contract tests.
- GitHub Actions certification workflow using Python 3.12 plus frontend typecheck/test/build.

## Biomedical representation boundary

EHR data is normalized as structured tabular data. Genomics is represented as a numeric sample-by-feature matrix and warns when dimensionality should be reduced before quantum encoding. Medical imaging accepts versioned embeddings or engineered image features rather than pushing raw high-resolution images directly into the bounded quantum circuit.

## Lineage and reproducibility

Every job stores model type, modality, dataset/preprocessing/encoding references, seed, model parameters, timestamps, status, progress, result/error payloads, cancellation state, and optional parent-job lineage. Reruns therefore produce a distinct job while retaining provenance.

## Certification

Run the repository's complete backend test suite with Python 3.12 and the frontend typecheck/test/build commands locally. The added workflow repeats those checks on GitHub for pull requests and Phase 12/main pushes.

This phase is implementation-complete when the local suite and GitHub Actions certification pass; a passing GitHub commit is evidence of repository CI execution, while local execution remains the final Windows/Python 3.12 confirmation.
