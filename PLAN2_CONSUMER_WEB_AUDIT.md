# Livenza.life V1 — Plan 2 Consumer Web & Stays Discovery Audit

## Baseline

- Source baseline: Plan 1 Foundation complete build derived from HOTFIX10 Rev D.
- Consumer application: new `web/` Next.js App Router source tree.
- Backend/customer foundation remains in the same release tree; Plan 2 does not replace the Flask back office.

## Implemented in this checkpoint

- Master `livenza.life` consumer shell and six-brand navigation.
- Locked neutral-first visual tokens and sub-brand accent system.
- Responsive/keyboard-aware mobile navigation and reduced-motion contract.
- Full approved Livenza.life homepage composition.
- `livenza.stays` city/query/stay-type search using `/api/v1/cities` and `/api/v1/properties`.
- Jaipur/Gurugram-compatible city route structure and public property cards.
- Property detail pages using Plan 1 `room_categories` only; no fabricated price, rating, review count, availability, amenity, policy, or FAQ data.
- Safe Plan 3 booking handoff page instead of a broken booking route.
- Store teaser and My Livenza handoff pages that explicitly state their later implementation phase.
- `livenza.fit`, `livenza.groom`, `livenza.skin`, and `livenza.media` early-access pages with no dead forms.
- About, Life, Contact, sitemap, robots, canonical metadata helper, and non-blocking analytics contract.
- Playwright mobile/desktop/keyboard discovery tests committed as source.
- Bundle-budget script and route-source audit script.
- Consumer deployment variables documented in `.env.example` and `README.md`.

## Fresh verification performed in the sandbox

### Plan 2 source contracts

Command:

```bash
pytest -q tests/test_plan2_*.py
```

Result: **21 passed, 0 failed**.

### Plan 1 foundation regression

Command:

```bash
PYTHONPATH=. pytest -q tests/test_livenza_*.py
```

Result: **31 passed, 10 skipped, 0 failed**.

The skipped tests require Flask/SQLAlchemy runtime packages that are not installed in this sandbox.

### Existing HOTFIX regression

Command: selected HOTFIX8/9/10 contract suite.

Result: **121 passed, 0 failed**.

### Offline TypeScript source verification

Command:

```bash
cd web && tsc -p tsconfig.offline.json --pretty false
```

Result: **PASS**. The offline config uses `web/tests/offline-stubs.d.ts` only to let the globally available TypeScript compiler parse/check the application source without installed Next/React packages. It does not replace the real Next.js type/build gate.

### Route-source audit

Command:

```bash
cd web && node scripts/check-route-sources.mjs
```

Result: **PASS** for the 12 top-level/handoff route sources covered by Plan 2.

## Production build gate still required

`npm install` could not complete in the execution sandbox and timed out; therefore there is no evidence in this environment for:

- `npm test -- --run` using Vitest/Testing Library;
- `npm run lint` using ESLint;
- `npm run build` using Next.js 16.3.3;
- `npm run check:bundle` against a real `.next/build-manifest.json`;
- `npm run test:e2e` using the packaged Playwright configuration.

Do not mark the Plan 2 production gate complete until those commands run successfully in CI/staging with Node.js 20.9+ and the pinned dependencies from `web/package.json`.

## Staging integration gate

Run Playwright with `PLAYWRIGHT_LIVE_API=1` and `LIVENZA_API_ORIGIN` pointed at the staged Flask API to verify the real search-to-property journey. The default E2E suite can seed API responses for isolated consumer UI verification; live staging must additionally exercise the real Plan 1 API.

## Data integrity rule

The consumer property UI deliberately does not manufacture unsupported commercial/property data. Where Plan 1 has not yet exposed media, amenities, policies, FAQ, price, distance, or review data, the page displays a transparent unpublished state.
