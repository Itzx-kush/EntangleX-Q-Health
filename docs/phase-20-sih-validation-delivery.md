# Phase 20 — SIH Validation, Final Demonstration and Delivery

## Positioning

> QuantaDetect is a reproducible hybrid quantum-classical research and decision-support platform for early disease-detection studies.

It does not claim clinical validation, autonomous diagnosis or quantum advantage unless sufficient evidence exists.

## Final demonstration flow

```text
Licensed biomedical sample
  -> input/security validation
  -> leakage-safe preprocessing
  -> classical and simulator quantum models
  -> repeated benchmarking and calibration
  -> classical/quantum explainability
  -> artifact-backed held-out prediction
  -> descriptive threshold/risk analysis
  -> experiment lineage and audit metadata
  -> evidence and SIH matrix export
```

## Validation gates

- Backend: `python -m pytest -q`, `python -m compileall -q app tests`, `pip check`.
- Frontend: `npm ci`, `npm run typecheck`, `npm test`, `npm run build`.
- API contract: `/health`, `/api/quantum/runtime/status`, `/api/platform/readiness`, `/api/platform/validation/matrix`.
- Security: PHI/PII scan, file validation, no-raw-record logging check, environment-only secret check.
- Dependency: operators should run `pip-audit -r backend/requirements.txt` and `npm audit --audit-level=high`; dependency findings do not become a fabricated clean security claim.
- Performance: use visible upload, quantum-resource and federated-site limits; benchmark results must be recorded rather than invented.
- Accessibility: keyboard navigation, visible focus, reduced-motion behavior, responsive layout and honest empty/offline states.
- Windows reproducibility: clean virtual environment, exact PowerShell commands, pinned lockfile and main-branch commit verification.
- Dataset provenance: record license, source URL, permitted use and de-identification review before demo upload.

## Final evidence package

- `docs/phase-19-scalability-security-hardware.md`
- `docs/phase-20-sih-validation-delivery.md`
- `GET /api/platform/validation/matrix` exported as `sih26139-validation-matrix.json`
- Existing experiment, benchmark, explainability and prediction artifacts
- CI run links and final Git commit
- Windows test/run transcript supplied by the project operator

The final delivery is a research prototype with explicit limitations, not a clinical product certificate.
