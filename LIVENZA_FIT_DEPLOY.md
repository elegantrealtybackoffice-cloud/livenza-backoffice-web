# Livenza.fit Fitness OS v0.4 — Staging / Deployment Runbook

This release keeps the v0.2 product implementation unchanged and adds guarded deployment helpers for Linux/macOS and Windows/PowerShell.

## Safety model

- The helper never guesses a database URL.
- `--migrate` / `-Migrate` refuse to run without `DATABASE_URL`.
- `--full` / `-Full` runs source verification first, then the additive Fit migration, then the real consumer-web gates.
- `--dry-run` / `-DryRun` prints the entire command sequence without modifying the database or installing packages.
- No production deploy is represented as complete until the real staging environment passes PostgreSQL, Next.js, ESLint, Playwright and provider integration checks.

## GitHub CI protection

v0.4 adds two repository workflows:

- `.github/workflows/livenza-fit-ci.yml` — automatic Fit-related pull-request/branch verification with no database credentials.
- `.github/workflows/livenza-fit-staging.yml` — manual, protected `staging` environment gate using `LIVENZA_STAGING_DATABASE_URL`.

See `LIVENZA_FIT_CI.md` for setup and safety details.

## Linux / macOS / Codex terminal

Preview the full sequence first:

```bash
scripts/deploy_livenza_fit.sh --dry-run --full
```

Portable verification only:

```bash
scripts/deploy_livenza_fit.sh --verify
```

Migration only:

```bash
export DATABASE_URL='postgresql://...'
scripts/deploy_livenza_fit.sh --migrate
```

Full staging gate:

```bash
export DATABASE_URL='postgresql://...'
scripts/deploy_livenza_fit.sh --full
```

## Windows PowerShell

Preview:

```powershell
.\scripts\Deploy-LivenzaFit.ps1 -DryRun -Full
```

Verification:

```powershell
.\scripts\Deploy-LivenzaFit.ps1 -Verify
```

Migration:

```powershell
$env:DATABASE_URL = 'postgresql://...'
.\scripts\Deploy-LivenzaFit.ps1 -Migrate
```

Full staging gate:

```powershell
$env:DATABASE_URL = 'postgresql://...'
.\scripts\Deploy-LivenzaFit.ps1 -Full
```

## What `--full` / `-Full` executes

1. Full Python repository tests.
2. Fit TypeScript domain compile and Fit Node tests.
3. Main offline and Fit UI TypeScript checks.
4. Python compilation, route audit, service-worker syntax and manifest parse.
5. `migrations/livenza_fit_v1.sql` through `psql` with `ON_ERROR_STOP=1`.
6. Consumer web dependency install, Vitest, ESLint, `next build`, bundle-budget check and Playwright E2E.

After these gates pass in staging, deploy the API/back-office service and the consumer Next.js site through their existing hosting pipelines, then smoke-test `/fit` plus authenticated `/api/v1/fit/*` endpoints.
