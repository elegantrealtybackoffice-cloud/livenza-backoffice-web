const test = require('node:test');
const assert = require('node:assert/strict');
const {
  clampRepSeconds,
  workoutDurationSeconds,
  calculateBmi,
  classifyBmi,
  estimateCalories,
  buildCountSequence,
} = require('../.build/fit/engine.js');

test('clampRepSeconds constrains unsafe or impractical timing values', () => {
  assert.equal(clampRepSeconds(0.1), 0.5);
  assert.equal(clampRepSeconds(3.5), 3.5);
  assert.equal(clampRepSeconds(99), 15);
});

test('workoutDurationSeconds includes rep work and rest only between sets', () => {
  assert.equal(workoutDurationSeconds({ sets: 3, reps: 10, repSeconds: 3, restSeconds: 60 }), 210);
});

test('calculateBmi returns metric BMI and rejects invalid dimensions', () => {
  assert.equal(calculateBmi(70, 175), 22.9);
  assert.equal(calculateBmi(0, 175), null);
  assert.equal(calculateBmi(70, 0), null);
});

test('classifyBmi follows standard adult screening bands', () => {
  assert.equal(classifyBmi(17.5), 'underweight');
  assert.equal(classifyBmi(22.9), 'healthy-range');
  assert.equal(classifyBmi(27.1), 'overweight');
  assert.equal(classifyBmi(31), 'obesity-range');
});

test('estimateCalories uses a MET-based estimate and guards invalid inputs', () => {
  assert.equal(estimateCalories(8, 70, 30), 294);
  assert.equal(estimateCalories(-1, 70, 30), 0);
});

test('buildCountSequence never skips requested rep numbers', () => {
  assert.deepEqual(buildCountSequence(5), [1, 2, 3, 4, 5]);
  assert.deepEqual(buildCountSequence(0), []);
  assert.equal(buildCountSequence(150).at(-1), 150);
});
