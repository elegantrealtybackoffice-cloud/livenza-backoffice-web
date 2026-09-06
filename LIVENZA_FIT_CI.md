# Livenza.fit v0.4 — CI and Staging Protection

v0.4 adds GitHub Actions gates without changing the Fit product behavior introduced in v0.2/v0.3.

## Pull request / branch CI

`.github/workflows/livenza-fit-ci.yml` runs automatically when Fit-related source changes reach a pull request or the `main`, `staging`, or `livenza-life-v1` branches. It deliberately has **no database credential** and cannot run the migration.

The CI gate runs:

1. Python dependency installation and full repository pytest suite.
2. Fit TypeScript domain compile and Node tests.
3. Offline and Fit UI TypeScript checks.
4. Python compilation, route audit, service-worker syntax and webmanifest parsing.
5. Consumer dependency installation, Vitest and ESLint.
6. Real Next.js production build and bundle-budget check.

A package-lock is not currently present in the inherited consumer source, so the workflow uses `npm install --no-audit --no-fund`. Move this to `npm ci` once a lockfile is intentionally generated and committed in the canonical Git repository.

## Protected staging gate

`.github/workflows/livenza-fit-staging.yml` is **manual only** (`workflow_dispatch`) and targets the protected GitHub environment named `staging`.

Configure one environment secret:

- `LIVENZA_STAGING_DATABASE_URL` — staging PostgreSQL URL only. Do not put a production URL in this environment.

The staging job refuses to continue if the secret is absent, installs a PostgreSQL client and Chromium, and then runs:

```bash
scripts/deploy_livenza_fit.sh --full
```

That sequence verifies source/tests first, applies only `migrations/livenza_fit_v1.sql` to the explicitly supplied staging database, then runs the consumer web test/lint/build/bundle/Playwright gates.

## Production policy

The workflow does **not** auto-deploy production and does not contain production credentials. Production routing remains a separate release decision after the protected staging gate is green.
