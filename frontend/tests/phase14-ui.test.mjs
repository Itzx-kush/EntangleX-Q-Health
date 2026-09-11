import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';

test('frontend exposes a centralized Phase 14 progress contract', () => {
  const project = readFileSync(new URL('../src/config/project.ts', import.meta.url), 'utf8');
  assert.match(project, /current: 14/);
  assert.match(project, /label: "Phase 14 of 20"/);
  assert.match(project, /rigorous benchmarking/);
});

test('redesigned visual layer is neutral and responsive', () => {
  const css = readFileSync(new URL('../src/styles.css', import.meta.url), 'utf8');
  assert.match(css, /--surface/);
  assert.match(css, /--accent/);
  assert.match(css, /@media \(max-width: 760px\)/);
  assert.match(css, /@keyframes pageIn/);
});
