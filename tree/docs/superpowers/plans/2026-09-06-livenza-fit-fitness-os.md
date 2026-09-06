# Livenza.fit Fitness OS Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Replace the Livenza.fit early-access page with a usable, offline-capable fitness operating system and provide an installable standalone PWA plus a drop-in Next.js patch.

**Architecture:** Build pure TypeScript fitness rules and exercise data first, then a client-side Next.js feature shell consuming those modules. Mirror the core behavior in a dependency-free standalone PWA for immediate local use. External health/music/live providers are represented through accurate adapter/status surfaces; real provider sync remains credential/native-companion gated.

**Tech Stack:** Next.js 16 / React 19 / TypeScript 5+, CSS Modules, Web Speech API, Web Audio/HTMLAudioElement, Web Crypto, localStorage, Service Worker/PWA; existing Flask/PostgreSQL API for future production sync.

**Spec:** `docs/superpowers/specs/2026-09-06-livenza-fit-fitness-os-design.md`

## Global Constraints

- Preserve the existing Livenza.life consumer/back-office architecture; this package is additive.
- Use the approved Livenza.fit logo and lime→green brand treatment.
- No production code without a failing test first for pure domain/data behavior.
- Do not fake external wearable/music/live connectivity.
- Do not put provider tokens/secrets in browser code.
- Offline workout, profile, PIN, health logging and local music must remain usable without internet.
- Exercise/health guidance is informational; include clear safety language.

---

### Task 1: Fitness domain engine

**Files:**
- Create: `tests/fit-engine.test.cjs`
- Create: `web/src/lib/fit/engine.ts`
- Create: `web/tsconfig.fit-domain.json`

**Interfaces:**
- Produces: `clampRepSeconds`, `workoutDurationSeconds`, `calculateBmi`, `classifyBmi`, `estimateCalories`, `buildCountSequence`.

- [x] Write tests first for tempo clamps, duration, BMI, BMI bands, calorie estimate and sequential rep counts.
- [x] Run the test command and confirm RED because the compiled engine does not exist.
- [x] Implement the minimal domain engine.
- [x] Compile with `tsc -p web/tsconfig.fit-domain.json` and run tests again.
- [x] Commit the green domain engine.

### Task 2: Exercise encyclopedia dataset

**Files:**
- Create: `tests/fit-exercises.test.cjs`
- Create: `web/src/lib/fit/exercises.ts`

**Interfaces:**
- Produces: `Exercise`, `EXERCISES`, `EXERCISE_CATEGORIES`, `getExerciseById`.

- [x] Write dataset contract tests requiring >=32 exercises, all required categories and complete coaching fields.
- [x] Verify RED.
- [x] Add the exercise dataset with defaults and illustration pose metadata.
- [x] Compile and verify tests GREEN.
- [x] Commit.

### Task 3: Local profile, PIN and persistence helpers

**Files:**
- Create: `tests/fit-storage.test.cjs`
- Create: `web/src/lib/fit/storage.ts`

**Interfaces:**
- Produces: storage key constants, `validatePinFormat`, `serializeWorkoutRecord`, `normalizeHealthLog`.
- Browser-only PIN hashing remains in the UI using Web Crypto.

- [x] Test validation/serialization behavior first.
- [x] Verify RED.
- [x] Implement pure storage helpers.
- [x] Compile and verify GREEN.
- [x] Commit.

### Task 4: Next.js Livenza.fit application UI

**Files:**
- Modify: `web/src/app/fit/page.tsx`
- Create: `web/src/app/fit/fit-app.tsx`
- Create: `web/src/app/fit/fit.module.css`
- Create: `web/src/app/fit/components/fit-logo.tsx`
- Create: `web/src/app/fit/components/workout-studio.tsx`
- Create: `web/src/app/fit/components/exercise-library.tsx`
- Create: `web/src/app/fit/components/health-dashboard.tsx`
- Create: `web/src/app/fit/components/music-studio.tsx`
- Create: `web/src/app/fit/components/integrations-panel.tsx`
- Create: `web/src/app/fit/components/plans-panel.tsx`
- Create: `web/src/app/fit/components/profile-panel.tsx`
- Create: `web/public/brand/livenza-fit-logo.png`

**Interfaces:**
- Consumes domain engine and exercise data.
- Produces the full `/fit` user experience.

- [x] Add an offline TypeScript source contract that fails while the app files are missing.
- [x] Implement the shell/nav and responsive visual system.
- [x] Implement Workout Studio with sequential voice counting, editable tempo, rest, pause/resume/stop and local history.
- [x] Implement searchable/filterable exercise library and coaching detail panel.
- [x] Implement Health, Plans, Music, Integrations and Profile panels.
- [x] Run offline type/syntax checks and domain tests.
- [x] Commit.

### Task 5: Installable/offline PWA assets

**Files:**
- Create: `web/public/fit.webmanifest`
- Create: `web/public/fit-sw.js`
- Create: `web/src/app/fit/components/pwa-boot.tsx`

- [x] Write a static service-worker contract test first.
- [x] Verify RED.
- [x] Add manifest, service worker and registration component.
- [x] Verify cache contract and JSON parsing.
- [x] Commit.

### Task 6: Runnable standalone offline build

**Files:**
- Create: `standalone/index.html`
- Create: `standalone/styles.css`
- Create: `standalone/app.js`
- Create: `standalone/manifest.webmanifest`
- Create: `standalone/sw.js`
- Create: `standalone/exercises.json`
- Create: `standalone/assets/livenza-fit-logo.png`

- [x] Generate standalone exercise JSON from the canonical dataset.
- [x] Build dependency-free UI with profile/PIN, exercise library, workout counter, health logs, music and integration status.
- [x] Add offline cache and installability.
- [x] Run `node --check`, JSON checks and a local HTTP smoke test.
- [x] Commit.

### Task 7: Integration architecture documentation and API scaffold

**Files:**
- Create: `docs/integrations/health-wearables.md`
- Create: `docs/integrations/music-live.md`
- Create: `docs/api/livenza-fit-api.md`
- Create: `migrations/livenza_fit_v1.sql`

- [x] Document Health Connect, Samsung Health companion, Apple HealthKit companion and Fitbit OAuth boundaries.
- [x] Document music/live adapter requirements and secret handling.
- [x] Define additive `/api/v1/fit` contracts and PostgreSQL tables without altering legacy customer identity.
- [x] Validate SQL for destructive statements and schema consistency.
- [x] Commit.

### Task 8: Verification and packaging

**Files:**
- Create: `VERIFY.md`
- Create: release ZIPs under `/mnt/data`.

- [x] Run all domain/data/static tests.
- [x] Run TypeScript source verification possible in the sandbox.
- [x] Start a local server and verify standalone shell/manifest/service worker return HTTP 200.
- [x] Scan for obvious token/secret names and ensure none are embedded.
- [x] Package `Livenza_Fit_Fitness_OS_v0.1_PATCH.zip`, `Livenza_Fit_Offline_PWA_v0.1.zip`, and a combined bundle.
- [x] Test ZIP integrity and list final artifacts.
