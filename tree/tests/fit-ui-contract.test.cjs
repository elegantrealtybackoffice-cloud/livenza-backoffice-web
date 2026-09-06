const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..', 'web', 'src', 'app', 'fit');

function read(name) { return fs.readFileSync(path.join(root, name), 'utf8'); }

test('fit route is a real Fitness OS rather than the early-access placeholder', () => {
  const page = read('page.tsx');
  assert.doesNotMatch(page, /EarlyAccessPage/);
  assert.match(page, /FitApp/);
});

test('fitness os exposes all primary modules', () => {
  const app = read('fit-app.tsx');
  for (const token of ['Today','Workout','Exercises','Plans','Health','Music','Live','Wearables','Profile']) {
    assert.match(app, new RegExp(token));
  }
});

test('workout studio contains voice synthesis and editable pacing controls', () => {
  const workout = read(path.join('components','workout-studio.tsx'));
  assert.match(workout, /speechSynthesis/);
  assert.match(workout, /repSeconds/);
  assert.match(workout, /Pause/);
  assert.match(workout, /Stop/);
});

test('brand logo is bundled in public assets', () => {
  assert.ok(fs.existsSync(path.join(__dirname, '..', 'web', 'public', 'brand', 'livenza-fit-logo.png')));
});
