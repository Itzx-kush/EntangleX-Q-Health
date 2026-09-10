# Phase 8 — Quantum runtime foundation and product UI

Phase 8 adds a simulator-first Qiskit runtime with deterministic seeds, explicit limits of eight qubits and 8,192 shots, GHZ diagnostic circuits, measured counts, transpiled depth/size/gate counts, duration, SQLite lineage, and JSON artifacts.

IBM Quantum capability is optional and environment-gated. Tokens are read only from environment variables and are never returned, logged, or persisted. Hardware submission remains disabled until explicit backend selection is implemented.

The frontend is redesigned as a complete responsive application with persistent navigation, pipeline progress, interactive workflow cards, a Quantum Runtime Lab, measured count visualization, evidence lineage, mobile navigation, loading/error states, and research safeguards.

This phase validates runtime mechanics only. Biomedical quantum encoding begins in Phase 9. No quantum advantage is claimed.
