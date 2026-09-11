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

if (typeof document !== "undefined") {
  const syncLegacyLabels = () => {
    document.querySelectorAll<HTMLElement>(".phase b").forEach((node) => {
      if (node.textContent !== PROJECT_PROGRESS.label) node.textContent = PROJECT_PROGRESS.label;
    });
    document.querySelectorAll<HTMLElement>(".phase small").forEach((node) => {
      if (node.textContent !== PROJECT_PROGRESS.workstream) node.textContent = PROJECT_PROGRESS.workstream;
    });
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let node: Node | null;
    while ((node = walker.nextNode())) {
      const text = node.nodeValue ?? "";
      const normalized = text.replaceAll("Phase 18 of 20", PROJECT_PROGRESS.label).replaceAll("18 / 20", PROJECT_PROGRESS.shortLabel);
      if (normalized !== text) node.nodeValue = normalized;
    }
  };
  const observer = new MutationObserver(syncLegacyLabels);
  observer.observe(document.documentElement, { childList: true, subtree: true, characterData: true });
  queueMicrotask(syncLegacyLabels);
}
