import assert from 'node:assert/strict';
import fs from 'node:fs';
import test from 'node:test';

const apiBase = fs.readFileSync(new URL('../src/services/apiBase.ts', import.meta.url), 'utf8');
const index = fs.readFileSync(new URL('../index.html', import.meta.url), 'utf8');

test('API base derives the backend from the current frontend host', () => {
  assert.match(apiBase, /location\.hostname === ["']localhost["']/);
  assert.match(apiBase, /127\.0\.0\.1/);
  assert.match(apiBase, /\$\{protocol\}\/\/\$\{hostname\}:8000/);
  assert.match(apiBase, /ENTANGLEX_API_URL/);
});

test('the HTML shell does not override runtime host resolution', () => {
  assert.doesNotMatch(index, /ENTANGLEX_API_URL\s*=/);
});
