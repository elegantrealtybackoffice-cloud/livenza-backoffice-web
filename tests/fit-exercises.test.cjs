const test = require('node:test');
const assert = require('node:assert/strict');
const { EXERCISES, EXERCISE_CATEGORIES, getExerciseById } = require('../.build/fit/exercises.js');

const REQUIRED = ['Chest','Back','Legs','Shoulders','Arms','Core','Cardio','Mobility','Yoga & Recovery'];

test('exercise encyclopedia contains at least 32 exercises across all required categories', () => {
  assert.ok(EXERCISES.length >= 32, `only ${EXERCISES.length} exercises`);
  for (const category of REQUIRED) {
    assert.ok(EXERCISE_CATEGORIES.includes(category), `missing category ${category}`);
    assert.ok(EXERCISES.some((exercise) => exercise.category === category), `no exercise in ${category}`);
  }
});

test('every exercise contains complete coaching and safe preset data', () => {
  for (const exercise of EXERCISES) {
    assert.match(exercise.id, /^[a-z0-9-]+$/);
    assert.ok(exercise.name.length >= 3);
    assert.ok(exercise.targets.length >= 1);
    assert.ok(exercise.steps.length >= 3, `${exercise.id} needs technique steps`);
    assert.ok(exercise.mistakes.length >= 2, `${exercise.id} needs common mistakes`);
    assert.ok(exercise.safety.length >= 12, `${exercise.id} needs safety guidance`);
    assert.ok(exercise.defaults.sets >= 1 && exercise.defaults.sets <= 8);
    assert.ok(exercise.defaults.reps >= 1 && exercise.defaults.reps <= 100);
    assert.ok(exercise.defaults.repSeconds >= 0.5 && exercise.defaults.repSeconds <= 15);
    assert.ok(exercise.defaults.restSeconds >= 0 && exercise.defaults.restSeconds <= 300);
    assert.ok(exercise.illustration.pose.length > 0);
  }
});

test('exercise ids are unique and lookup returns the canonical record', () => {
  const ids = EXERCISES.map((exercise) => exercise.id);
  assert.equal(new Set(ids).size, ids.length);
  const pushup = getExerciseById('push-up');
  assert.equal(pushup?.name, 'Push-Up');
  assert.equal(getExerciseById('does-not-exist'), undefined);
});
