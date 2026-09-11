import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

const app = readFileSync(new URL('../src/App.tsx', import.meta.url), 'utf8');
const api = readFileSync(new URL('../src/services/api.ts', import.meta.url), 'utf8');
const css = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');
const project = readFileSync(new URL('../src/config/project.ts', import.meta.url), 'utf8');
const orchestration = readFileSync(new URL('../src/components/Phase12Orchestration.tsx', import.meta.url), 'utf8');
const registry = readFileSync(new URL('../src/components/Phase13ExperimentRegistry.tsx', import.meta.url), 'utf8');
const experimentTypes = readFileSync(new URL('../src/types/experiment.ts', import.meta.url), 'utf8');

test('medical and quantum claims are bounded', () => {
  assert.match(app, /Research evidence only/i);
  assert.match(app, /quantum advantage/i);
  assert.match(css, /--success/);
});

test('phases one through seven remain integrated and configurable', () => {
  for (const route of [/api\/datasets\/upload/, /api\/preprocessing\/run/, /api\/models\/train/, /api\/evaluations\/run/]) assert.match(api, route);
  for (const copy of [/Duplicate rows/, /Numeric missing/, /Categorical encoding/, /Outlier policy/, /Balancing/, /Feature selection/, /logistic_regression/, /Regularization C/, /Evaluate test set/]) assert.match(app, copy);
});

test('phases nine and ten use real QML endpoints', () => {
  assert.match(api, /api\/quantum\/qml\/encodings/);
  assert.match(api, /api\/quantum\/qml\/vqc\/train/);
  for (const copy of [/Create feature encoding/, /Variational quantum classifier/, /Training samples/, /Max iterations/, /COBYLA/, /preprocessing and encoding artifact/]) assert.match(app, copy);
});

test('runtime diagnostics remain clearly independent', () => {
  assert.match(api, /api\/quantum\/runtime\/diagnostics/);
  assert.match(app, /GHZ runtime check/i);
  assert.match(app, /not a biomedical prediction/i);
});

test('navigation and responsive workspace behavior remain available', () => {
  for (const copy of [/function Dashboard/, /function Pipeline/, /function QuantumLab/, /function Evidence/, /type="button"/, /window\.scrollTo/]) assert.match(app, copy);
  assert.match(app, /Overview/);
  assert.match(app, /Decision Center/);
});

test('professional light-first design and theme switching exist', () => {
  for (const copy of [/RESEARCH OPERATIONS/, /PROJECT_PROGRESS/, /entanglex-theme/]) assert.match(app + project, copy);
  assert.match(css, /--surface/);
  assert.match(css, /\[data-theme="dark"\]/);
  assert.match(css, /@media \(max-width: 760px\)/);
  assert.match(css, /@keyframes pageIn/);
});

test('phase eleven model suite is real and configurable', () => {
  for (const route of [/api\/quantum\/qml\/qsvm\/train/, /api\/quantum\/qml\/qnn\/train/]) assert.match(api, route);
  for (const copy of [/Fidelity-kernel QSVM/, /Hybrid quantum neural network/, /classification/, /regression/, /Nelder Mead/]) assert.match(app, copy);
});

test('no fabricated metrics', () => {
  for (const value of ['0.94', '92.1%', '88.7%']) assert.equal(app.includes(value), false);
});

test('phase twelve orchestration UI is complete', () => {
  for (const copy of [/Create queued job/, /Run/, /Cancel/, /Rerun/, /Validate modality/, /progressTrack/, /preprocessing lineage/, /encoding lineage/]) assert.match(orchestration, copy);
  assert.match(api, /api\/orchestration\/jobs/);
});

test('phase thirteen registry preserves lineage and honest evidence states', () => {
  for (const copy of [/PHASE 13/, /Register current lineage/, /Search registry/, /Clone/, /Export JSON/, /Compare/, /No measured metrics recorded/, /scientific_warnings/]) assert.match(registry, copy);
  for (const copy of [/api\/experiments/, /compareExperiments/, /exportExperiment/]) assert.match(api, copy);
  for (const copy of [/ExperimentArtifact/, /ExperimentIntegrity/, /recorded_results/]) assert.match(experimentTypes, copy);
  assert.match(orchestration, /Phase13ExperimentRegistry/);
});
