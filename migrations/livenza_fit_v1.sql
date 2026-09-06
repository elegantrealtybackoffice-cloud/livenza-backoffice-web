-- Livenza.fit Fitness OS v0.2 additive schema for the current Livenza.life V1 branch.
-- This branch uses customer(id) as INTEGER. No existing table is altered or dropped.

CREATE TABLE IF NOT EXISTS livenza_fit_profiles (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL UNIQUE REFERENCES customer(id),
    units VARCHAR(16) NOT NULL DEFAULT 'metric',
    height_cm REAL NULL,
    default_rep_seconds REAL NOT NULL DEFAULT 3.0,
    goal VARCHAR(64) NOT NULL DEFAULT 'general_fitness',
    preferences_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_profiles_customer ON livenza_fit_profiles(customer_id);

CREATE TABLE IF NOT EXISTS livenza_fit_workouts (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    client_record_id VARCHAR(128) NOT NULL,
    exercise_id VARCHAR(96) NOT NULL,
    exercise_name VARCHAR(160) NOT NULL,
    sets INTEGER NOT NULL,
    reps INTEGER NOT NULL,
    rep_seconds REAL NOT NULL,
    duration_seconds INTEGER NOT NULL DEFAULT 0,
    estimated_calories REAL NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'livenza_fit_web',
    metadata_json TEXT NOT NULL DEFAULT '{}',
    completed_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_fit_workout_customer_client_record UNIQUE(customer_id, client_record_id)
);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_workouts_customer_completed ON livenza_fit_workouts(customer_id, completed_at);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_workouts_exercise ON livenza_fit_workouts(exercise_id);

CREATE TABLE IF NOT EXISTS livenza_fit_health_logs (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    provider_record_id VARCHAR(192) NULL,
    source VARCHAR(64) NOT NULL DEFAULT 'manual',
    recorded_at TIMESTAMP NOT NULL,
    weight_kg REAL NULL,
    height_cm REAL NULL,
    bmi REAL NULL,
    steps INTEGER NULL,
    active_calories REAL NULL,
    total_calories REAL NULL,
    activity_minutes INTEGER NULL,
    resting_heart_rate INTEGER NULL,
    sleep_minutes INTEGER NULL,
    raw_summary_json TEXT NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_fit_health_customer_source_record UNIQUE(customer_id, source, provider_record_id)
);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_health_customer_recorded ON livenza_fit_health_logs(customer_id, recorded_at);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_health_source ON livenza_fit_health_logs(source);

CREATE TABLE IF NOT EXISTS livenza_fit_plans (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    name VARCHAR(160) NOT NULL,
    difficulty VARCHAR(32) NOT NULL DEFAULT 'beginner',
    schedule_json TEXT NOT NULL DEFAULT '[]',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_plans_customer ON livenza_fit_plans(customer_id);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_plans_active ON livenza_fit_plans(is_active);

CREATE TABLE IF NOT EXISTS livenza_fit_connections (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    provider VARCHAR(48) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'disconnected',
    credential_ref VARCHAR(256) NOT NULL DEFAULT '',
    scopes_json TEXT NOT NULL DEFAULT '[]',
    provider_metadata_json TEXT NOT NULL DEFAULT '{}',
    last_sync_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_fit_connection_customer_provider UNIQUE(customer_id, provider)
);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_connections_customer ON livenza_fit_connections(customer_id);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_connections_provider ON livenza_fit_connections(provider);
CREATE INDEX IF NOT EXISTS ix_livenza_fit_connections_status ON livenza_fit_connections(status);
