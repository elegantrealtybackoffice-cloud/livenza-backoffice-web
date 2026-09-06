const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');

test('fit migration is additive and targets this branch customer table',()=>{
  const sql=fs.readFileSync(path.join(__dirname,'..','migrations','livenza_fit_v1.sql'),'utf8');
  assert.doesNotMatch(sql,/\bDROP\s+(TABLE|COLUMN)\b/i);
  assert.doesNotMatch(sql,/\bALTER\s+TABLE\b/i);
  for(const table of ['livenza_fit_profiles','livenza_fit_workouts','livenza_fit_health_logs','livenza_fit_plans','livenza_fit_connections']) assert.match(sql,new RegExp(`CREATE TABLE IF NOT EXISTS ${table}`));
  assert.match(sql,/REFERENCES\s+customer\(id\)/i);
  assert.doesNotMatch(sql,/REFERENCES\s+customers\(id\)/i);
});

test('fit API documentation covers core resources and server-side integration secrets',()=>{
  const doc=fs.readFileSync(path.join(__dirname,'..','docs','api','livenza-fit-api.md'),'utf8');
  for(const route of ['/api/v1/fit/profile','/api/v1/fit/workouts','/api/v1/fit/health/logs','/api/v1/fit/integrations']) assert.match(doc,new RegExp(route.replaceAll('/','\\/')));
  assert.match(doc,/server-side/i);
  assert.match(doc,/never.*browser/i);
});
