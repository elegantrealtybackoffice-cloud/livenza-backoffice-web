# Public Midnight Blue Website Launch Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Publish the approved midnight-blue theme across the public Livenza site, with six Gurugram property pages, mapped owner media, a sector-level interactive map, and WhatsApp enquiry.

**Architecture:** Keep the existing Next.js app, API client, booking and account flows. Add a small curated brochure data layer for the six named properties and known media; merge live API details when available. Apply a shared public visual system through the existing site shell and route styles. Deploy only to Render's `livenza.life` service after verification.

**Tech Stack:** Next.js 16, React 19, TypeScript, CSS, Vitest, Render.

**Spec:** `docs/superpowers/specs/2026-10-31-livenza-stays-interactive-brochure-design.md` (in the `livenza-life-v1` worktree).

## Global Constraints

- Only the public website changes; back-office screens remain untouched.
- Preserve customer, booking, payment, store and API behavior.
- Use the owner's logo and property-mapped media for G 38 Getaway, The Sienna and The Elara.
- The Azure, The Avelia and The Maralia have no approved images in the supplied package.
- Sector 38, 51 and 52 positions are schematic until exact addresses and Google links are supplied.
- WhatsApp enquiries use `+91 7688845555`.

## Review Focus

- A missing public API still leaves the six brochure pages and enquiry links usable.
- Unknown properties continue through the existing API and 404 handling.
- A sector marker never pretends to be a precise Google location.
- Rooms and booking links appear only from published API data.
- Mobile navigation and map links remain keyboard accessible.

---

### Task 1: Curated content and assets

**Files:** Create `web/src/lib/brochure.ts`, `web/src/lib/brochure.test.ts`; add approved media under `web/public/stays/`.

- [ ] Write tests for six names, sectors, media ownership, safe lookup and WhatsApp links.
- [ ] Run the tests and see the missing feature fail.
- [ ] Implement the data module and copy approved assets.
- [ ] Run tests and typecheck.
- [ ] Commit Task 1.

### Task 2: Shared theme and overview

**Files:** Modify `web/src/components/site-header.tsx`, `site-footer.tsx`, `web/src/styles/tokens.css`, `brand.css`, `web/src/app/page.tsx`, `page.module.css`, `web/src/app/stays/page.tsx`, `stays.css`; create `web/src/components/gurugram-map.tsx`.

- [ ] Add a page-level test for six named links and the map introduction.
- [ ] Run it and see it fail.
- [ ] Implement the shared shell, illustrated home and Stays map/gallery.
- [ ] Run test, typecheck, lint and build.
- [ ] Commit Task 2.

### Task 3: Property pages and remaining public routes

**Files:** Modify `web/src/app/stays/[city]/[property]/page.tsx`, `web/src/components/property-gallery.tsx`, `web/src/app/stays/property.css`, `web/src/app/stays/[city]/page.tsx`, `web/src/styles/ecosystem.css`, `web/src/app/store/store.css`.

- [ ] Add tests for curated route fallback and property-specific enquiry.
- [ ] Run them and see them fail.
- [ ] Render mapped galleries and optional video, preserve live rooms and booking links, and apply the shared public theme.
- [ ] Run tests, typecheck, lint and build.
- [ ] Commit Task 3.

### Task 4: Verify and publish

- [ ] Browser-check desktop and mobile overview, map pin navigation, a media-rich page, a media-pending page, WhatsApp and booking handoff.
- [ ] Confirm the branch diff contains no back-office or pre-existing dirty edits.
- [ ] Push and integrate into Render's watched `unified-livenza-platform` branch.
- [ ] Watch the Render deployment and verify the live site URLs.
