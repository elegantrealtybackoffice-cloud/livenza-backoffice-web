# Livenza.fit API v1 Contract

**Base:** `/api/v1/fit`  
**Identity:** the existing authenticated Livenza customer session. Livenza.fit does not create a parallel customer account.

The Fit browser/PWA is local-first. Without a customer session it continues to run locally; authenticated users can synchronize supported records to the shared Livenza account.

## Profile

### `GET /api/v1/fit/profile`
Returns the signed-in customer's Fit preferences. When no row exists, the API returns safe defaults.

### `PUT /api/v1/fit/profile`
Accepted fields include `units` (`metric` or `imperial`), `height_cm`, `default_rep_seconds` (0.5–15.0), `goal`, and a bounded preferences object.

The local device PIN is never sent to this endpoint. It stays on-device as a salted hash; Livenza account authentication remains separate.

## Workouts

### `GET /api/v1/fit/workouts?limit=50&before=<ISO8601>`
Returns only the authenticated customer's workout history, newest first.

### `POST /api/v1/fit/workouts`

```json
{
  "client_record_id": "device-generated-idempotency-id",
  "exercise_id": "push-up",
  "exercise_name": "Push-Up",
  "sets": 3,
  "reps": 10,
  "rep_seconds": 3.5,
  "duration_seconds": 105,
  "estimated_calories": 20.2,
  "source": "livenza_fit_web",
  "completed_at": "2026-09-06T04:00:00Z"
}
```

`client_record_id` is unique per customer so an offline retry returns the existing workout rather than duplicating it.

## Health logs

### `GET /api/v1/fit/health/logs?from=<ISO8601>&to=<ISO8601>&limit=100`
Returns the signed-in customer's normalized health summaries with source attribution.

### `POST /api/v1/fit/health/logs`

```json
{
  "recorded_at": "2026-09-06T04:10:00Z",
  "weight_kg": 70,
  "height_cm": 175,
  "steps": 5234,
  "activity_minutes": 35,
  "resting_heart_rate": 62,
  "source": "manual"
}
```

When valid height and weight are present, the server recomputes BMI and ignores any arbitrary client-supplied BMI. Provider records can use `provider_record_id`; `(customer_id, source, provider_record_id)` is the idempotency boundary when that key exists.

## Plans

### `GET /api/v1/fit/plans`
Lists customer-created synchronized plans.

### `POST /api/v1/fit/plans`
Creates a plan with `name`, `difficulty`, `schedule`, and optional `is_active`.

### `PATCH /api/v1/fit/plans/<plan_id>`
Updates only a plan owned by the authenticated customer.

## Integrations

### `GET /api/v1/fit/integrations`
Returns safe connection metadata only. `credential_ref`, OAuth tokens and provider secrets are never serialized.

### `POST /api/v1/fit/integrations/<provider>/connect`
Supported native health providers (`health_connect`, `samsung_health`, `apple_health`) return a `requires_companion` state until authorization is completed in an eligible native companion app.

Cloud/media providers such as Fitbit, Spotify, Apple Music and live-video fail closed with `fit_provider_not_configured` until their approved server-side adapter and credentials are configured through Livenza's protected Integrations/Vault layer.

### `DELETE /api/v1/fit/integrations/<provider>`
Removes the Livenza-side connection record. Provider-side token revocation should be performed by the future configured provider adapter when applicable.

## Secret handling

OAuth client secrets, refresh tokens, Apple private keys, Samsung partner credentials, live-video secrets and similar provider credentials are **server-side secrets**. They must never be embedded in browser JavaScript, web manifests, localStorage, public environment variables, source ZIPs or API responses.

## Error format

Fit endpoints use the existing Livenza V1 API error envelope:

```json
{
  "ok": false,
  "error": "default_rep_seconds must be at least 0.5.",
  "code": "fit_validation_error"
}
```

Provider errors use provider-safe codes such as `fit_provider_not_supported` or `fit_provider_not_configured`; raw provider token material and sensitive upstream error payloads must not be forwarded to the browser.
