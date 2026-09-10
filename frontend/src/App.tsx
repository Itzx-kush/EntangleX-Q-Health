import { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import { getHealth } from "./services/api";
import type { HealthStatus } from "./types/health";

const stages = ["Upload dataset", "Prepare data", "Select features", "Reduce dimensions", "Train models", "Compare", "Explain", "Predict"];

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then(setHealth).catch((reason: unknown) => {
      setError(reason instanceof Error ? reason.message : "Backend unavailable");
    });
  }, []);

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand"><div className="mark" aria-hidden="true">Ξ</div><div><strong>EntangleX</strong><span>Q-Health</span></div></div>
        <div className={`status ${health?.status === "ok" ? "ok" : ""}`}><span />{health ? `Platform ${health.status}` : error ? "Backend offline" : "Checking platform"}</div>
      </header>
      <main>
        <section className="hero">
          <div className="eyebrow">SIH26139 • HYBRID QUANTUM–CLASSICAL ML</div>
          <h1>Biomedical model research, without unsupported claims.</h1>
          <p>A reproducible platform for ingesting biomedical data, training classical and quantum-enhanced models, comparing measured performance, explaining feature influence, and producing research decision-support predictions.</p>
          <div className="actions"><button disabled title="Available in Phase 2">Load demo dataset</button><button className="secondary" disabled title="Available in Phase 2">Upload dataset</button></div>
          <p className="phase">Phase 1 foundation • Data workflows unlock after validated ingestion is implemented</p>
        </section>
        <section className="panel">
          <div className="panelHead"><div><div className="eyebrow">RESEARCH WORKFLOW</div><h2>One defensible path from data to evidence</h2></div><span className="tag">Simulator-first</span></div>
          <div className="flow">{stages.map((stage, index) => <div className="step" key={stage}><span>{String(index + 1).padStart(2, "0")}</span><b>{stage}</b></div>)}</div>
        </section>
        <section className="grid">
          <article className="card"><div className="icon blue">D</div><h3>Backend &amp; storage</h3><p>{health ? `${health.service} v${health.version} • database ${health.database.status}` : "Waiting for live health data."}</p></article>
          <article className="card"><div className="icon violet">Q</div><h3>Quantum capability</h3><p>{health ? `${health.quantum.backend}: ${health.quantum.simulator}` : "Capability probe not loaded."}</p></article>
          <article className="card"><div className="icon cyan">R</div><h3>Reproducibility first</h3><p>Dataset hashes, seeds, pipeline configuration, software versions and measured timings will be stored per experiment.</p></article>
        </section>
        <section className="notice"><b>Research use only.</b> This platform is a research and decision-support prototype. Predictions based on benchmark or user-provided datasets are not a substitute for professional medical diagnosis or clinical validation.</section>
      </main>
      <footer>EntangleX Q-Health • No fake metrics • No assumed quantum advantage</footer>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
