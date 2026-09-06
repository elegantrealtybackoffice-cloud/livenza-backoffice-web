const test = require('node:test');
const assert = require('node:assert/strict');
const { validatePinFormat, serializeWorkoutRecord, normalizeHealthLog, STORAGE_KEYS } = require('../.build/fit/storage.js');

test('validatePinFormat accepts only 4 to 8 digits', () => {
  assert.equal(validatePinFormat('1234'), true);
  assert.equal(validatePinFormat('12345678'), true);
  assert.equal(validatePinFormat('123'), false);
  assert.equal(validatePinFormat('123456789'), false);
  assert.equal(validatePinFormat('12a4'), false);
});

test('serializeWorkoutRecord normalizes numeric workout history values', () => {
  const record = serializeWorkoutRecord({ exerciseId:'push-up', exerciseName:'Push-Up', reps:10.9, sets:3.9, repSeconds:3.47, durationSeconds:104.8, completedAt:'2026-09-06T03:00:00.000Z' });
  assert.deepEqual(record, { exerciseId:'push-up', exerciseName:'Push-Up', reps:10, sets:3, repSeconds:3.5, durationSeconds:105, completedAt:'2026-09-06T03:00:00.000Z' });
});

test('normalizeHealthLog rejects impossible height/weight and preserves optional activity metrics', () => {
  assert.equal(normalizeHealthLog({ weightKg:0, heightCm:175 }), null);
  assert.deepEqual(normalizeHealthLog({ weightKg:70.04, heightCm:175.2, steps:5234.9, activityMinutes:34.8, restingHeartRate:62.4 }), {
    weightKg:70,
    heightCm:175.2,
    steps:5234,
    activityMinutes:35,
    restingHeartRate:62,
  });
});

test('storage keys are namespaced under fit', () => {
  for (const value of Object.values(STORAGE_KEYS)) assert.match(value, /^fit\./);
});
