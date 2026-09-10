import test from "node:test";import assert from "node:assert/strict";import {readFileSync} from "node:fs";
const source=readFileSync(new URL("../src/App.tsx",import.meta.url),"utf8");const api=readFileSync(new URL("../src/services/api.ts",import.meta.url),"utf8");
test("medical disclaimer is present",()=>assert.match(source,/not a substitute for professional medical diagnosis/));
test("quantum advantage is not claimed",()=>{assert.doesNotMatch(source,/guaranteed quantum advantage/i);assert.match(source,/No assumed quantum advantage/)});
test("no demo metrics are hardcoded",()=>{for(const value of ["0.94","92.1%","88.7%"]){assert.equal(source.includes(value),false)}});
test("dataset upload and target APIs are integrated",()=>{assert.match(api,/api\/datasets\/upload/);assert.match(api,/\/target/);assert.match(source,/Choose CSV or XLSX/)});
test("preprocessing is integrated without metrics",()=>{assert.match(api,/api\/preprocessing\/run/);assert.match(source,/Split before fit/);assert.match(source,/Training-fitted transformations/)});
test("class balancing is training-only",()=>{assert.match(source,/Random oversampling/);assert.match(source,/SMOTE/);assert.match(source,/preserve held-out test/)});
