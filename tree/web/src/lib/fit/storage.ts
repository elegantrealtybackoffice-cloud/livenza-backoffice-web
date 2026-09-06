export const STORAGE_KEYS = {
  profile: 'fit.profile',
  settings: 'fit.settings',
  healthLogs: 'fit.healthLogs',
  workoutHistory: 'fit.workoutHistory',
  customPlans: 'fit.customPlans',
  pinCredential: 'fit.pinCredential',
} as const;

export type WorkoutRecordInput = {
  exerciseId: string;
  exerciseName: string;
  reps: number;
  sets: number;
  repSeconds: number;
  durationSeconds: number;
  completedAt: string;
};

export type WorkoutRecord = WorkoutRecordInput;

export type HealthLogInput = {
  weightKg: number;
  heightCm: number;
  steps?: number;
  activityMinutes?: number;
  restingHeartRate?: number;
};

export type HealthLog = Required<Pick<HealthLogInput, 'weightKg' | 'heightCm'>> &
  Partial<Pick<HealthLogInput, 'steps' | 'activityMinutes' | 'restingHeartRate'>>;

export function validatePinFormat(pin: string): boolean {
  return /^\d{4,8}$/.test(pin);
}

function roundOne(value: number): number {
  return Math.round(value * 10) / 10;
}

export function serializeWorkoutRecord(input: WorkoutRecordInput): WorkoutRecord {
  return {
    exerciseId: String(input.exerciseId),
    exerciseName: String(input.exerciseName),
    reps: Math.max(0, Math.floor(input.reps)),
    sets: Math.max(0, Math.floor(input.sets)),
    repSeconds: roundOne(Math.max(0, input.repSeconds)),
    durationSeconds: Math.max(0, Math.round(input.durationSeconds)),
    completedAt: String(input.completedAt),
  };
}

export function normalizeHealthLog(input: HealthLogInput): HealthLog | null {
  if (!Number.isFinite(input.weightKg) || !Number.isFinite(input.heightCm)) return null;
  if (input.weightKg < 20 || input.weightKg > 400 || input.heightCm < 80 || input.heightCm > 250) return null;

  const result: HealthLog = {
    weightKg: roundOne(input.weightKg),
    heightCm: roundOne(input.heightCm),
  };

  if (Number.isFinite(input.steps)) result.steps = Math.max(0, Math.floor(input.steps as number));
  if (Number.isFinite(input.activityMinutes)) result.activityMinutes = Math.max(0, Math.round(input.activityMinutes as number));
  if (Number.isFinite(input.restingHeartRate)) result.restingHeartRate = Math.max(20, Math.min(240, Math.round(input.restingHeartRate as number)));
  return result;
}
