# Phase 19 — Scalability, Privacy, Security and Hardware Readiness

## Delivered controls

- Bounded dataset uploads, quantum qubits/shots, prediction batches, federated sites/rounds and artifact retention values.
- SQLite-backed audit events with indexes on timestamp and path. Request bodies and biomedical values are never persisted by the audit middleware.
- PHI/PII-like column and sample-key warnings with a de-identification checklist.
- Path traversal, extension, content-type and size validation metadata endpoint.
- Environment-only provider secret detection: the API reports whether a token exists but never returns the token.
- Explicit simulator/hardware compatibility checks with qubit, shot, circuit-depth and timeout limits.
- Hardware status distinguishes simulator readiness from unavailable queue, cost, calibration and noise evidence.
- Federated-ready privacy sandbox using weighted parameter aggregation and site metadata only. Raw patient records are never exchanged.
- Existing orchestration retains queued/running/completed/failed/cancel-requested/cancelled/retry states; the platform limits and governance endpoints make operational bounds visible.
- The release checklist includes compile checks, tests, `pip check`, `pip-audit` and `npm audit` commands. Dependency findings are reviewed explicitly rather than hidden behind a fabricated clean claim.

## API surface

```text
GET  /api/platform/limits
GET  /api/platform/security/checklist
POST /api/platform/security/scan
GET  /api/platform/audit/events
GET  /api/platform/hardware/status
POST /api/platform/hardware/compatibility
POST /api/platform/federated/sandbox
GET  /api/platform/readiness
GET  /api/platform/validation/matrix
```

## Federated sandbox contract

Each simulated institution submits only a site identifier, sample count, feature/parameter dimension, an optional dataset fingerprint and a local parameter vector for weighted aggregation. The endpoint returns aggregated parameters and non-sensitive site metadata. It does not implement production hospital federated learning, secure aggregation, differential privacy or a clinical deployment boundary. Those limitations are deliberately visible.

## Hardware contract

Hardware execution is opt-in and simulator-first. A real run is not claimed merely because a backend name is compatible. A valid hardware evidence record must include provider job ID, backend, queue timing, cost metadata, shots, circuit resources and calibration/noise metadata. Without those fields the UI reports an unavailable or not-run state.
