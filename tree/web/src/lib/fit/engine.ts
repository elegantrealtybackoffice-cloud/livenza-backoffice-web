export type WorkoutPrescription = {
  sets: number;
  reps: number;
  repSeconds: number;
  restSeconds: number;
};

export type BmiBand =
  | 'underweight'
  | 'healthy-range'
  | 'overweight'
  | 'obesity-range';

function finiteOr(value: number, fallback: number): number {
  return Number.isFinite(value) ? value : fallback;
}

export function clampRepSeconds(value: number): number {
  const normalized = finiteOr(value, 3);
  return Math.min(15, Math.max(0.5, Math.round(normalized * 10) / 10));
}

export function workoutDurationSeconds(input: WorkoutPrescription): number {
  const sets = Math.max(1, Math.floor(finiteOr(input.sets, 1)));
  const reps = Math.max(1, Math.floor(finiteOr(input.reps, 1)));
  const repSeconds = clampRepSeconds(input.repSeconds);
  const restSeconds = Math.max(0, finiteOr(input.restSeconds, 0));
  const active = sets * reps * repSeconds;
  const rests = Math.max(0, sets - 1) * restSeconds;
  return Math.round((active + rests) * 10) / 10;
}

export function calculateBmi(weightKg: number, heightCm: number): number | null {
  if (!Number.isFinite(weightKg) || !Number.isFinite(heightCm) || weightKg <= 0 || heightCm <= 0) {
    return null;
  }
  const heightM = heightCm / 100;
  const bmi = weightKg / (heightM * heightM);
  return Math.round(bmi * 10) / 10;
}

export function classifyBmi(bmi: number): BmiBand {
  if (bmi < 18.5) return 'underweight';
  if (bmi < 25) return 'healthy-range';
  if (bmi < 30) return 'overweight';
  return 'obesity-range';
}

export function estimateCalories(met: number, weightKg: number, durationMinutes: number): number {
  if (
    !Number.isFinite(met) ||
    !Number.isFinite(weightKg) ||
    !Number.isFinite(durationMinutes) ||
    met <= 0 ||
    weightKg <= 0 ||
    durationMinutes <= 0
  ) {
    return 0;
  }
  const kcalPerMinute = (met * 3.5 * weightKg) / 200;
  return Math.round(kcalPerMinute * durationMinutes);
}

export function buildCountSequence(reps: number): number[] {
  const safeReps = Math.max(0, Math.min(500, Math.floor(finiteOr(reps, 0))));
  return Array.from({ length: safeReps }, (_, index) => index + 1);
}
