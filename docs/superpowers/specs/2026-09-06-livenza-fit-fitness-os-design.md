# Livenza.fit Fitness OS — Product & Technical Design

**Date:** 2026-09-06  
**Status:** Approved under the user's standing instruction to proceed with the recommended plan without routine approval pauses.  
**Baseline:** Existing Livenza.life consumer Next.js application with `/fit` currently acting as an early-access route; existing Flask/PostgreSQL platform remains the authoritative operational/API layer.

## 1. Goal

Turn `livenza.life/fit` into a complete Livenza.fit fitness application with the same core experience available online and offline. The first deliverable must be genuinely usable without external credentials: workout discovery, exercise education, rep/timer engine, voice counting, editable pacing, local profiles/PIN, health calculations/logging, plans, local music playback, and installable offline PWA behavior. Connected integrations are added through explicit adapters and must never pretend to be synced when provider credentials or native-platform bridges are absent.

## 2. Product Principles

- One Livenza.fit product, not separate unrelated desktop and web products.
- Web-first PWA is the shared feature surface; it can be installed as a desktop application and continue working offline.
- Preserve the existing Livenza.life customer identity when integrated into production. A local PIN is a device/session lock, not a replacement for server authentication.
- Offline actions save locally first; connected deployments can sync through the Livenza API layer.
- Exercise presets are sensible defaults, always editable by the user.
- Voice counting, sound cues, and music controls must coexist; spoken prompts should temporarily duck local music volume where supported.
- Health and calorie values are informational estimates, not diagnoses.
- External provider status is always explicit: connected, disconnected, unavailable, or requires companion app.

## 3. Information Architecture

Primary modules:

1. **Today** — workout readiness, quick start, weekly progress, current streak, health summary.
2. **Workout Studio** — exercise queue, sets/reps, rep tempo, rest timer, voice count, pause/resume/stop, elapsed/remaining time.
3. **Exercise Library** — categorized exercises with illustrations, target muscles, equipment, difficulty, detailed method, mistakes, safety guidance, default sets/reps/tempo/rest.
4. **Plans** — beginner/intermediate/advanced templates and customizable schedules.
5. **Health** — weight, height, BMI, calories, activity minutes, steps, heart-rate fields, trend summaries.
6. **Music** — local audio player offline plus connected-provider entry points and curated workout playlist intents.
7. **Live & Video** — recorded technique content and live-session entry points; provider-backed playback is enabled only when configured.
8. **Wearables** — Google Fit/Health Connect, Samsung Health, Apple Health/Apple Watch, Fitbit status and sync controls.
9. **Profile & Settings** — user ID, local PIN lock, units, audio/voice options, default rep tempo, reduced motion, privacy/export/reset.

## 4. Workout Engine

The workout engine is a pure TypeScript module so web/PWA, future native shells, and tests can share the same rules.

Core interfaces:

```ts
export type WorkoutPrescription = {
  sets: number;
  reps: number;
  repSeconds: number;
  restSeconds: number;
};

export type BmiBand = 'underweight' | 'healthy-range' | 'overweight' | 'obesity-range';

export function clampRepSeconds(value: number): number;
export function workoutDurationSeconds(input: WorkoutPrescription): number;
export function calculateBmi(weightKg: number, heightCm: number): number | null;
export function classifyBmi(bmi: number): BmiBand;
export function estimateCalories(met: number, weightKg: number, durationMinutes: number): number;
```

Rep tempo is constrained to 0.5–15 seconds per rep. The UI default for conventional bodyweight reps is 3 seconds unless an exercise preset specifies another value. The counter schedules one spoken number per rep and does not skip numbers.

## 5. Exercise Dataset

The seed dataset contains at least 32 exercises across:

- Chest
- Back
- Legs
- Shoulders
- Arms
- Core
- Cardio
- Mobility
- Yoga / recovery

Every exercise record contains:

- stable slug/id
- name and category
- target muscles
- equipment
- difficulty
- concise overview
- 3+ ordered technique steps
- common mistakes
- safety note
- default sets, reps, rep timing and rest
- estimated MET where appropriate
- original vector-style illustration metadata rather than scraped copyrighted photography

## 6. Offline & Desktop Strategy

The initial desktop deliverable is an installable PWA, because it provides one shared feature surface across Windows/macOS/Linux without duplicating UI and domain logic. The service worker caches the shell, exercise data, logo, and core scripts. User-created records are stored in browser local storage for the standalone package; the production Livenza deployment can later use IndexedDB plus background sync/API synchronization.

A future Tauri shell can wrap the same web application if native installers, filesystem access, background services, or Bluetooth integrations justify it. This design avoids prematurely maintaining two independent application stacks.

## 7. Identity & PIN

Production identity remains the Livenza customer account. The offline PWA supports a local profile with a user ID/display name and optional PIN.

PIN requirements:

- 4–8 digits
- never stored in plaintext
- salted SHA-256 using Web Crypto for the standalone implementation
- local unlock only; no banking/payment/security credential reuse
- reset clears local profile data unless a production authenticated recovery path exists

## 8. Health & Wearable Integrations

### Android / Google
Use Android Health Connect as the primary modern Android health bridge. A native Android companion can request granular permissions and sync supported records to the Livenza API. The web UI labels this connector **Google Fit / Health Connect** for user recognition while the implementation targets Health Connect where available.

### Samsung Health
Use Samsung Health Data SDK from an Android companion app. The web/PWA cannot directly access the Samsung Health local data store, so the connector explicitly shows when a companion app/partner configuration is required.

### Apple Health / Apple Watch
Use HealthKit from an iOS/watchOS companion. A normal website cannot directly query the HealthKit store. The companion syncs authorized summaries to the Livenza backend for presentation in Livenza.fit.

### Fitbit
Use Fitbit Web API OAuth for user-authorized cloud data where supported. Tokens are server-side secrets; refresh/access tokens must never be stored in browser source.

### Health metrics
The first release calculates BMI locally from height/weight and estimates exercise calories with MET-based calculations. It can display manually entered steps, calories, heart rate and activity minutes before provider sync exists.

## 9. Music

Offline mode includes a local-file audio player using browser File APIs. Online provider adapters expose connection/search/playlist actions only when configured. Provider integrations must respect account/subscription and playback-policy constraints; the application must not claim arbitrary universal playback from every platform.

The app includes intent presets such as Warm-up, Strength, HIIT, Run, Mobility and Cool-down. Spoken rep counts can reduce local music volume temporarily and restore it afterwards.

## 10. Live & Video

The UI includes video technique cards and live-session scheduling/entry points. In the standalone package, these are clearly demo/local states. Production can connect a video CDN/streaming provider and video-conferencing/live-class provider through the API/integration layer.

## 11. Brand & UI

- Use the user-approved `livenza.fit` wordmark asset.
- Primary fit accent: lime-to-green (`#C7F000` → `#00C96B`) with dark graphite/navy foundations.
- Dense but calm fitness dashboard, large touch targets, responsive layout.
- The counter is visually dominant during an active set.
- Animation respects reduced-motion preference.
- No Apple/Samsung/Fitbit logos are bundled unless licensed/provider assets are explicitly supplied; use text labels and neutral connector icons.

## 12. Data & Sync Boundaries

Standalone local records:

```text
fit.profile
fit.settings
fit.healthLogs
fit.workoutHistory
fit.customPlans
fit.pinCredential
```

Production API additions should be additive under `/api/v1/fit/...` and use the existing customer identity rather than creating a second customer table. Suggested resources:

```text
GET/POST /api/v1/fit/profile
GET/POST /api/v1/fit/workouts
GET/POST /api/v1/fit/health/logs
GET/POST /api/v1/fit/plans
GET      /api/v1/fit/integrations
POST     /api/v1/fit/integrations/:provider/connect
POST     /api/v1/fit/integrations/:provider/sync
```

## 13. Error Handling

- Invalid workout numbers are clamped or rejected with readable validation.
- Counter timing survives pause/resume without duplicate counts.
- Voice synthesis unavailable: continue visual counter silently.
- Local audio unsupported/failed: preserve workout flow and show player error only.
- External connector absent: show exact prerequisite rather than generic failure.
- Storage quota/error: continue active workout in memory and surface an export/retry action.
- Network loss: automatically return to offline/local state; never discard an active set.

## 14. Testing

- Unit tests for timing, duration, BMI, BMI banding and calorie math.
- Dataset contract tests for exercise completeness and preset ranges.
- Static checks for standalone JavaScript and JSON manifests.
- TypeScript source checks using offline declarations where project dependencies are not installed.
- Service-worker asset list checks.
- Manual staging/browser gates remain mandatory for production Next.js build, microphone/audio/voice behavior, installability and provider OAuth/native-companion flows.

## 15. First Build Acceptance Criteria

The delivered build is accepted when:

- `/fit` is no longer an early-access placeholder in the supplied patch.
- at least 32 categorized exercise records are available;
- a user can select an exercise and run a set with editable reps, sets, rep seconds and rest seconds;
- voice counting runs from 1 through the requested rep count without intentional skipping;
- pause/resume/stop work;
- local profile + hashed PIN work in the standalone PWA;
- BMI and estimated calories calculate locally;
- health logs and workout history persist locally;
- local audio files can play;
- integration cards explain and expose supported connector paths without fake sync state;
- the standalone PWA is installable/offline-capable;
- unit/static verification passes;
- a drop-in `web/` patch and a runnable standalone package are both produced.
