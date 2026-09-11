import test from 'node:test';import assert from 'node:assert/strict';import{readFileSync}from'node:fs';
test('merged prototype exposes Phase 14 progress label',()=>{const css=readFileSync(new URL('../src/phase12-ui.css',import.meta.url),'utf8');assert.match(css,/Phase 14 of 20/);assert.match(css,/rigorous benchmarking/)});
