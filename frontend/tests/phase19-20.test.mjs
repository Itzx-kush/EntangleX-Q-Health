import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

test('Governance Center is loaded by the production shell', () => {
  const index = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');
  const script = fs.readFileSync(new URL('../public/phase19-20.js', import.meta.url), 'utf8');
  assert.match(index, /phase19-20\.js/);
  assert.match(script, /\/api\/platform\/readiness/);
  assert.match(script, /\/api\/platform\/validation\/matrix/);
  assert.match(script, /federated\/sandbox/);
});

test('Governance Center keeps a visible research boundary', () => {
  const script = fs.readFileSync(new URL('../public/phase19-20.js', import.meta.url), 'utf8');
  assert.match(script, /Raw records/);
  assert.match(script, /quantum advantage/);
});
