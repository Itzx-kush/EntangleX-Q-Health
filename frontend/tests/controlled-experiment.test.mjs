import test from 'node:test';
import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
const center=readFileSync(new URL('../src/experiment-center.ts',import.meta.url),'utf8');
const project=readFileSync(new URL('../src/config/project.ts',import.meta.url),'utf8');
test('controlled experiment workspace is wired into the application',()=>{assert.match(project,/experiment-center/);for(const value of [/controlled-experiments/,/comparison_fingerprint/,/preprocessing_run_id/,/logistic_regression/,/random_forest/,/vqc/,/qsvm/,/qnn/])assert.match(center,value)});
test('job UI reports real checkpoints and independent model outcomes',()=>{for(const value of [/Verified checkpoint/,/succeeded/,/failed/,/cancelled/,/Request cancellation/,/Rerun as new experiment/])assert.match(center,value)});
test('quantum execution and evidence limits are explicit',()=>{for(const value of [/exact local statevector simulation/i,/not (physical )?hardware/i,/CV: not executed/i,/Missing metrics remain NA/i,/No winner is inferred automatically/i])assert.match(center,value)});
test('no fabricated comparison numbers are present',()=>{for(const value of ['94.2%','91.5%','0.94'])assert.equal(center.includes(value),false)});
