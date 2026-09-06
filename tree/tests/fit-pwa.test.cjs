const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const pub=path.join(__dirname,'..','web','public');

test('fit web manifest is installable and branded',()=>{
  const manifest=JSON.parse(fs.readFileSync(path.join(pub,'fit.webmanifest'),'utf8'));
  assert.equal(manifest.name,'Livenza.fit Fitness OS');
  assert.equal(manifest.start_url,'/fit');
  assert.equal(manifest.display,'standalone');
  assert.ok(manifest.icons.some((icon)=>icon.src.includes('livenza-fit')));
});

test('fit service worker caches the offline shell essentials',()=>{
  const sw=fs.readFileSync(path.join(pub,'fit-sw.js'),'utf8');
  for(const token of ['/fit','/fit.webmanifest','/brand/livenza-fit-logo.png']) assert.match(sw,new RegExp(token.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')));
  assert.match(sw,/caches\.open/);
  assert.match(sw,/fetch/);
});

test('PwaBoot registers the fit service worker',()=>{
  const source=fs.readFileSync(path.join(__dirname,'..','web','src','app','fit','components','pwa-boot.tsx'),'utf8');
  assert.match(source,/serviceWorker/);
  assert.match(source,/fit-sw\.js/);
});
