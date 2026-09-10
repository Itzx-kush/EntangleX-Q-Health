import { useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";

import { getHealth, previewDataset, selectTarget, uploadDataset } from "./services/api";
import type { DatasetPreview, DatasetSummary } from "./types/dataset";
import type { HealthStatus } from "./types/health";

const stages = ["Upload dataset", "Prepare data", "Select features", "Reduce dimensions", "Train models", "Compare", "Explain", "Predict"];

function App() {
  const [health, setHealth] = useState<HealthStatus | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dataset, setDataset] = useState<DatasetSummary | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const input = useRef<HTMLInputElement | null>(null);

  useEffect(() => { getHealth().then(setHealth).catch(() => setHealth(null)); }, []);

  async function handleUpload() {
    if (!file) return;
    setBusy(true); setMessage(null);
    try {
      const result = await uploadDataset(file);
      setDataset(result);
      setPreview(await previewDataset(result.id));
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Upload failed");
    } finally { setBusy(false); }
  }

  async function handleTarget(value: string) {
    if (!dataset || !value) return;
    setBusy(true); setMessage(null);
    try { setDataset(await selectTarget(dataset.id, value)); }
    catch (error) { setMessage(error instanceof Error ? error.message : "Target validation failed"); }
    finally { setBusy(false); }
  }

  function clearDataset() {
    setFile(null); setDataset(null); setPreview(null); setMessage(null);
    if (input.current) input.current.value = "";
  }

  const columns = dataset ? [...dataset.numeric_columns, ...dataset.categorical_columns, ...dataset.datetime_columns] : [];

  return (
    <div className="app">
      <header className="topbar"><div className="brand"><div className="mark">Ξ</div><div><strong>EntangleX</strong><span>Q-Health</span></div></div><div className={`status ${health?.status === "ok" ? "ok" : ""}`}><span />{health ? `Platform ${health.status}` : "Backend offline"}</div></header>
      <main>
        <section className="hero compact"><div className="eyebrow">PHASE 2 • DATASET INGESTION</div><h1>Bring biomedical data into a defensible workflow.</h1><p>Upload a CSV or XLSX benchmark dataset. EntangleX validates the file, inspects its schema, records a deterministic hash, and reports quality issues without silently repairing them.</p></section>
        <section className="workspace"><div className="uploadCard"><div className="panelHead"><div><div className="eyebrow">DATASET</div><h2>Upload and inspect</h2></div><span className="tag">Maximum 25 MB</span></div><input ref={input} type="file" accept=".csv,.xlsx" hidden onChange={(event: { target: HTMLInputElement }) => setFile(event.target.files?.[0] ?? null)} /><button onClick={() => input.current?.click()} className="drop">{file ? <><b>{file.name}</b><span>{(file.size / 1024).toFixed(1)} KB selected</span></> : <><b>Choose CSV or XLSX</b><span>Files are validated before storage</span></>}</button><div className="actions"><button onClick={handleUpload} disabled={!file || busy}>{busy ? "Validating…" : "Upload dataset"}</button>{file && <button className="secondary" onClick={clearDataset}>Clear</button>}</div>{message && <div className="error">{message}</div>}</div></section>
        {dataset && <section className="result"><div className="resultHead"><div><div className="eyebrow">DATASET REGISTERED</div><h2>{dataset.name}</h2><p>{dataset.original_filename} • SHA-256 {dataset.sha256.slice(0, 12)}…</p></div><label>Target column<select value={dataset.target_column ?? ""} onChange={(event: { target: HTMLSelectElement }) => handleTarget(event.target.value)}><option value="">Select target</option>{columns.map((column) => <option key={column}>{column}</option>)}</select></label></div><div className="metrics"><Metric label="Samples" value={dataset.rows} /><Metric label="Features" value={dataset.columns} /><Metric label="Missing" value={dataset.total_missing_values} /><Metric label="Duplicates" value={dataset.duplicate_rows} /></div>{dataset.class_distribution && <div className="classes"><b>Binary target distribution</b>{Object.entries(dataset.class_distribution).map(([label, count]) => <span key={label}>Class {label}: {count}</span>)}</div>}{dataset.warnings.map((warning) => <div className="warning" key={warning}>{warning}</div>)}<div className="schema"><div><b>Numerical</b><span>{dataset.numeric_columns.join(", ") || "None"}</span></div><div><b>Categorical</b><span>{dataset.categorical_columns.join(", ") || "None"}</span></div></div>{preview && <div className="tableWrap"><table><thead><tr>{preview.columns.map((column) => <th key={column}>{column}</th>)}</tr></thead><tbody>{preview.rows.map((row, index) => <tr key={index}>{preview.columns.map((column) => <td key={column}>{row[column] === null ? "—" : String(row[column])}</td>)}</tr>)}</tbody></table><p>Showing {preview.rows.length} of {preview.total_rows} rows. Raw values are preview-only.</p></div>}</section>}
        <section className="panel"><div className="panelHead"><div><div className="eyebrow">RESEARCH WORKFLOW</div><h2>One defensible path from data to evidence</h2></div><span className="tag">Simulator-first</span></div><div className="flow">{stages.map((stage, index) => <div className={`step ${index === 0 ? "active" : ""}`} key={stage}><span>{String(index + 1).padStart(2, "0")}</span><b>{stage}</b></div>)}</div></section>
        <section className="notice"><b>Research use only.</b> This platform is a research and decision-support prototype. Predictions based on benchmark or user-provided datasets are not a substitute for professional medical diagnosis or clinical validation.</section>
      </main>
      <footer>EntangleX Q-Health • Measured evidence • No assumed quantum advantage</footer>
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string | number }) { return <div><span>{label}</span><b>{value}</b></div>; }
createRoot(document.getElementById("root")!).render(<App />);
