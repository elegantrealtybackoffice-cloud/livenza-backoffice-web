const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const root=path.join(__dirname,'..');
const read=(p)=>fs.readFileSync(path.join(root,p),'utf8');

test('consumer API exposes authenticated Livenza.fit sync helpers',()=>{
  const api=read('web/src/lib/api.ts');
  for(const name of ['getFitProfile','saveFitProfile','getFitWorkouts','syncFitWorkout','getFitHealthLogs','syncFitHealthLog','getFitIntegrations','connectFitIntegration']){
    assert.match(api,new RegExp(`export (async )?function ${name}\\b`));
  }
  assert.match(api,/\/api\/v1\/fit\/workouts/);
  assert.match(api,/\/api\/v1\/fit\/health\/logs/);
});

test('workout and health saves remain local-first and attempt online sync',()=>{
  const workout=read('web/src/app/fit/components/workout-studio.tsx');
  const health=read('web/src/app/fit/components/health-dashboard.tsx');
  assert.match(workout,/syncFitWorkout/);
  assert.match(workout,/localStorage\.setItem/);
  assert.match(health,/syncFitHealthLog/);
  assert.match(health,/localStorage\.setItem/);
});

test('profile keeps device PIN local while syncing non-secret preferences',()=>{
  const profile=read('web/src/app/fit/components/profile-panel.tsx');
  assert.match(profile,/saveFitProfile/);
  assert.match(profile,/createPinCredential/);
  assert.doesNotMatch(read('web/src/lib/api.ts'),/pinCredential|New PIN|pin_hash/i);
});
