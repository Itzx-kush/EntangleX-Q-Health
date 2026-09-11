# Phase 13 — Experiment Registry and Reproducibility

## Delivered

- Immutable SQLite-backed experiment records with parent lineage and clone operations.
- Environment capture: Python, Node when supplied, operating system, platform, application version, Git commit, and package versions.
- Explicit seed snapshots and nondeterminism warnings.
- SHA-256 manifests for file artifacts, with verified, unverified, missing, modified, and invalid-path states.
- Clone blocking when source artifacts are missing or altered.
- Compatible descriptive comparisons constrained by task type, model family, and modality.
- Honest missing-result handling; no winner labels and no quantum-advantage claims.
- JSON and ZIP evidence exports, dataset cards, and model cards with `not_recorded` states.
- FastAPI routes under `/api/experiments` and a registry workspace inside the existing Phase 12 orchestration surface.

## Evidence boundary

Reference-only records remain visibly unverified. A registry entry does not manufacture a metric or convert a research run into a clinical claim. The JSON/ZIP export is an evidence package, not a certification.

## Validation

Use the backend and frontend commands in the repository README. CI validates the Phase 13 backend registry tests and frontend source/build checks on the draft pull request.
