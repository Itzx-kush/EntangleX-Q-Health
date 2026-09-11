export const PROJECT_PROGRESS = Object.freeze({
  current: 14,
  total: 20,
  label: "Phase 14 of 20",
  shortLabel: "14 / 20",
  workstream: "Experiment registry + rigorous benchmarking",
});

export const PRODUCT = Object.freeze({
  name: "EntangleX",
  product: "QuantaDetect",
  descriptor: "Biomedical research workspace",
  disclaimer: "Research use only · Not a substitute for professional medical diagnosis",
});

(globalThis as { ENTANGLEX_PROJECT_PROGRESS?: typeof PROJECT_PROGRESS }).ENTANGLEX_PROJECT_PROGRESS = PROJECT_PROGRESS;
