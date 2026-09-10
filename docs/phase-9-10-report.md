# Phases 9–10 — Quantum encoding and variational classifier

Phase 9 consumes the selected leakage-safe preprocessing artifact. It selects one feature per qubit, fits min/max angle scaling on training features only, transforms and clips test features to `[0, π]`, constructs linear or ring-entangled `RY` circuits, records transpiled resources, and persists compressed encoded arrays with lineage.

Phase 10 trains a real parameterized quantum circuit using Qiskit statevectors and SciPy COBYLA. Binary cross-entropy is evaluated from circuit probabilities; seeds, ansatz repetitions, sample caps, optimizer iterations, losses, parameters, resources, held-out metrics, duration, and lineage are persisted. Outputs depend on the data and configuration. No metrics are hardcoded and no quantum advantage is claimed.

The Phase 8 GHZ diagnostic remains separate because it tests runtime health, not biomedical modeling.
