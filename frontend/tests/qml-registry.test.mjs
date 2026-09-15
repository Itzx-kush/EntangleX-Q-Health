import test from'node:test';import assert from'node:assert/strict';import{readFileSync}from'node:fs';
const types=readFileSync(new URL('../src/types/qml.ts',import.meta.url),'utf8');
const explainability=readFileSync(new URL('../src/components/Phase16QuantumExplainability.tsx',import.meta.url),'utf8');
const api=readFileSync(new URL('../src/services/api.ts',import.meta.url),'utf8');
test('quantum registry uses an explicit discriminated frontend union',()=>{for(const value of [/VQCRegistryRun/,/QSVMRun/,/QNNRun/,/model_type:'vqc'/,/model_type:'qsvm'/,/model_type:'qnn'/,/QuantumModelRun=VQCRegistryRun\|QSVMRun\|QNNRun/])assert.match(types,value)});
test('quantum explainability consumes the unified registry without duplicating VQC',()=>{assert.match(explainability,/listQuantumModels/);assert.doesNotMatch(explainability,/listVQCRuns/);assert.match(explainability,/item\.model_type/);assert.match(explainability,/item\.status/);assert.match(api,/api\/quantum\/qml\/models/)});
