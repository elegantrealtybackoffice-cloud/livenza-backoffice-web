# Livenza.fit Health & Wearables Integration Architecture

**Design date:** 2026-09-06

The web/PWA remains the common user interface, but not every health platform exposes private sensor/health data directly to a browser. Livenza.fit therefore uses provider-specific adapters and native companion apps only where the platform requires them.

## Data contract

Livenza.fit normalizes permitted provider data into these user-facing metric groups:

- activity: steps, distance, active minutes, exercise sessions;
- energy: active calories and total calories when a provider supplies them;
- body: weight, height, body-fat percentage/body composition where permitted;
- cardio: resting heart rate and workout heart rate summaries where permitted;
- recovery: sleep duration/stages where permitted;
- provenance: provider, source device, recorded time, sync time, and permission scope.

Provider records are never silently merged into a made-up value. The API preserves source/provider metadata so a user can understand where a number came from.

## Google Fit / Health Connect

**Implementation target:** Android Health Connect.

The user-facing connector can be named **Google Fit / Health Connect** for recognition, but the current Android integration path should be Health Connect. Android documents Health Connect as the health-and-fitness data platform exposed through its SDK, with permissions for reading/writing supported records. On Android 14 and later Health Connect is part of the Android framework; earlier supported Android versions use the Health Connect app.

Architecture:

```text
Health Connect on Android
  -> Livenza.fit Android companion
  -> user grants granular record permissions
  -> companion normalizes authorized summaries
  -> POST /api/v1/fit/integrations/health-connect/sync
  -> Livenza.fit web / desktop PWA
```

Do not request data types until a Livenza.fit feature actually needs them. Store the authorization/sync status, not Android permission UI state invented by the web client.

Official reference: https://developer.android.com/health-and-fitness/health-connect/get-started

## Samsung Health / Galaxy Watch

Use **Samsung Health Data SDK**, not the deprecated older Samsung Health SDK for Android. Samsung's 2026 Data SDK documentation identifies v1.1.0 and supports selected Samsung Health data including activity, body composition, exercise, heart rate, sleep, nutrition and other wellness records. It runs through an Android application and requires an eligible Samsung Health environment; it is not a browser API.

Architecture:

```text
Galaxy Watch / connected device
  -> Samsung Health on phone
  -> Livenza.fit Android companion + Samsung Health Data SDK
  -> user grants requested Samsung Health data permissions
  -> Livenza API sync
  -> shared Livenza.fit UI
```

Distribution must follow Samsung's current app verification/partner requirements. No Samsung token, key, SDK binary, or branded provider asset is bundled in this patch.

Official references:
- https://developer.samsung.com/health/data/overview.html
- https://developer.samsung.com/health/data/guide/introduction.html
- https://developer.samsung.com/health/data/release-note.html

## Apple Health + Apple Watch

HealthKit is the native repository for health and fitness data on iPhone and Apple Watch. Access is per-data-type and user controlled. A normal web page cannot directly query the device HealthKit store, so Livenza.fit needs an iOS/watchOS companion for genuine Apple Health/Watch sync.

Architecture:

```text
Apple Watch / iPhone HealthKit
  -> Livenza.fit iOS companion
  -> granular HealthKit authorization
  -> companion sends only authorized normalized summaries
  -> Livenza API
  -> shared web/PWA dashboard
```

The backend must tolerate permissions changing or being revoked later. Health data is treated as sensitive; only the minimum necessary fields are retained and each sync is attributed to its source.

Official references:
- https://developer.apple.com/documentation/healthkit/
- https://developer.apple.com/documentation/HealthKit/authorizing-access-to-health-data

## Fitbit

Fitbit provides a Web API for activity-tracker and user health/activity data. User data must be accessed with user authorization and appropriate OAuth scopes. Livenza.fit should implement Fitbit OAuth on the server and store token material in a protected secret store / Livenza Vault, never in browser JavaScript or localStorage.

Architecture:

```text
Livenza.fit web
  -> GET /api/v1/fit/integrations/fitbit/connect
  -> server starts Fitbit authorization
  -> callback exchanges authorization code
  -> access/refresh tokens stored server-side
  -> scheduled/on-demand Fitbit sync
  -> normalized health_log records
```

Official API explorer: https://dev.fitbit.com/build/reference/web-api/explore/

## BMI and calorie estimates

The offline app can calculate BMI locally from height and weight and use a MET-based estimate for exercise calories:

```text
kcal/min = MET × 3.5 × body_weight_kg / 200
```

These values are estimates for fitness tracking, not diagnoses or clinical measurements. Provider-reported energy values should remain distinguishable from locally estimated values.

## Consent, privacy and deletion

- never connect a provider without explicit user action;
- request only scopes necessary for enabled features;
- expose the provider/source beside synced metrics;
- allow disconnect and token revocation;
- disconnect must stop future sync but should not silently erase historic records unless the user chooses deletion;
- health data must not be used for unrelated advertising or profile enrichment;
- do not expose raw integration credentials in browser responses, logs or exports.
