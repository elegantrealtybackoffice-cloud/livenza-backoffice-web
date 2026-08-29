# Tesla OS 27 — Version 27.0.1 (Build 27A101)

Livenza Life operations workspace presented through the Tesla OS 27 vibrant macOS 27 desktop interface, rebuilt from the official Apple macOS 27 UI Kit measurements and interaction patterns.

> **Tesla OS 27 is a cumulative release.** The macOS-style interface is only the newest presentation layer. The backend and operational features from the earlier Web 1.7.0, 1.7.1, 1.8.0 and 1.9.0 releases remain included in this build.

## Interface
- **Hotfix 10 Light Shell** Home: dedicated lightweight CSS/JS instead of the legacy module, TV and general application bundles.
- **Navigation fail-safe:** core Home controls are real links first and JavaScript enhancements second, so a failed Home script cannot make Suites/Dock/menu navigation dead.
- First-run/reset Home uses the **Livenza.life · LIVE ELEVATED.** scenic wallpaper with a compact 34 px macOS-style menu bar.
- Curated colorful Dock shortcuts for **Suites, Agreement Studio, Rooms, Queries, Reviews, Banking and System Settings**, with restrained magnification and reduced-motion fallback.
- Widgets are asleep/hidden by default and open only from the top-bar Widgets control; no weather/live-operation polling runs on idle Home.
- Livenza Companion is dock-adjacent at the lower-right and loads its panel only when requested rather than occupying the desktop centre.
- System Settings uses its own bright lightweight stylesheet with aligned sidebars, forms, switches, wallpaper controls and a persistent Dock.
- The approved Livenza brand system uses navy `#061A3A`, emerald `#35D05B` and cyan `#10C8CF` while keeping working content surfaces bright and professional.
- Every Hotfix 10 CSS/JS URL carries asset revision **`27A101-H10L-20260827D`** so immutable browser/CDN caches cannot silently reuse an older Hotfix shell.
- Tesla OS identity remains **Tesla OS 27 / Version 27.0.1 / Build 27A101**.

## Complete Backend Included

### Agreements, Masters & Occupancy
- **Agreement Studio** with create, edit, preview, PDF and sharing workflows.
- **Landlord & Tenant Masters** with reusable profiles, agreement autofill, secure document handling, archive/reactivation and compatibility with existing records.
- Rooms inventory, vacancy and resident/tenant occupancy records.
- Existing agreement and tenant data remains compatible with the cumulative release.

### Electricity, Billing, Banking & Vault
- **Electricity Bill Studio** with connections, provider directory, bill uploads, due dates, bill register and payment/reminder workflows.
- Billing and collections workspace.
- Banking document upload and reconciliation workflows.
- **Livenza Vault** for protected configuration/secrets with role-aware access and secure reveal/delete controls.
- Historical schema migrations remain included for deployment compatibility.

### Queries, Reviews, Food & Operations
- Query Manager and live lead/follow-up workflows, including sheet-style management and exports.
- Google Review Studio.
- Food Hub / delivery-partner integration workflows and partner portals.
- Video Wall and commercial-screen workflows.
- Existing Rentok/billing operational integrations remain available according to permissions and configured connections.

### Integrations & Communications
- Central Integrations Center / Internet Accounts architecture.
- WhatsApp workspace and delivery hooks.
- Gmail/Email workspace.
- Google Drive / cloud-file workspace.
- Role-aware provider connections with protected Admin configuration for credentials and secrets.
- Existing integration data and secure server-side configuration are preserved.

### AI, Mascot & Device Experience
- **3D Livenza Companion** architecture and per-user companion preferences.
- Live companion/assistant behavior and Ask Livenza entry points.
- Responsive desktop, tablet, mobile, fullscreen and TV/low-capability compatibility layers retained.
- WebAuthn/passkey support and pattern-login support remain part of the authentication stack where configured.

### Letterhead Studio
- **Letterhead Studio** for official Livenza documents.
- Template library and editor workflows.
- Ask Livenza AI assisted document creation.
- Supporting-file/attachment handling and review workflow.
- Approval/finalization gates and immutable PDF issuance flow.
- Email and WhatsApp delivery actions.
- Letterhead Document Vault for finalized documents.

### Security & Permissions
- Existing role permissions remain authoritative across Suites.
- Admin-only controls remain protected on the server side.
- Vault-backed secrets and protected document flows remain in place.
- Existing secure POST handlers, authentication checks and audit-sensitive workflows are retained.

## Suites Available
Depending on the signed-in user's permissions, the Suites launcher can expose:

- System Settings
- Agreement Studio
- Landlord Master
- Tenant Master
- Rooms
- Residents
- Queries
- Reviews
- Video Wall
- Food
- Billing
- Banking
- Electricity
- WhatsApp
- Email
- Drive
- Letterhead Studio

The launcher is permission-aware; an unavailable Suite can be hidden without being removed from the product.

## Cumulative Release Lineage

### Web 1.7.0 — Utilities, Vault & AI Foundation
Introduced the Electricity/Vault generation of backend capabilities, including electricity provider/connections workflows, bill register/payment/reminder foundations, protected Vault storage and AI live-mascot foundation.

### Web 1.7.1 — Masters & Agreement Data Reuse
Added the dedicated Landlord Master and Tenant Master architecture, secure master documents, agreement autofill/annexure support, migration compatibility and the grouped application navigation work.

### Web 1.8.0 — 3D Host, Integrations & Responsive/TV Layer
Added the genuine 3D host architecture, centralized role-aware Integrations Center, TV/legacy navigation compatibility, responsive layout hardening and cross-device UI quality improvements while retaining the 1.7.x backend.

### Web 1.9.0 — Letterhead Studio & Advanced Document Workflows
Added Letterhead Studio, AI-assisted drafting, templates, attachments, review/finalization, PDF issuance, delivery and Document Vault integration while retaining all 1.8.0 functionality.

### Tesla OS 27 — Version 27.0.1 (Build 27A101)
Repackages the complete cumulative Livenza operations platform under the Tesla OS 27 nomenclature and macOS-inspired application shell. This release changes the product identity and shell experience without intentionally deleting the earlier backend modules.

## Deployment Compatibility
- Existing business data and databases are retained; do not delete historical migration files.
- Existing secure POST handlers, role permissions and server-side authorization remain authoritative.
- Existing Agreements, Rooms, Queries, Billing, Banking, Electricity, Food, Video Wall, WhatsApp, Email, Drive, Integrations and Letterhead workflows remain available through Suites according to permissions.
- Historical database migration filenames are retained only for schema compatibility and do not represent the current product version.

## Deployment Verification
After deployment, first verify `/version` and response headers expose asset revision **`27A101-H10L-20260827D`**. Home must request only `home_light.css` + `home_light.js` for its Hotfix 10 shell and must not request the legacy module/application/TV bundles. Confirm the Livenza.life default wallpaper, seven curated Dock icons, lower-right Companion, on-demand Widgets, immediate View/Suites menus and refined bright System Settings match the packaged Chromium previews. Full steps are in `VERIFY_DEPLOY.txt`.

## Hotfix 6 — macOS 27 Exact-Kit Pass

This pass tightens the visual shell against the supplied Apple macOS 27 UI Kit rather than adding a separate theme layer. It locks the extracted 34px menu bar, 58px Dock, 36px Dock icons, 45px Dock stride, 4px running indicator, 16px windows, 52/40/77px toolbar variants, 256px sidebar, 344px notification/widget width, 20px notification radius, 26px alert radius, 24px regular controls/menu rows, 13/16 body typography, and two-ring focus treatment.

Dock magnification now uses pointer distance so adjacent icons react smoothly. Transient UI uses brief scale/opacity materialization with a complete `prefers-reduced-motion` fallback. Motion durations are web implementation choices aligned with the HIG behavior; they are not represented as private Apple runtime timing constants.

## Hotfix 7 — Browser-OS Clean Shell

Hotfix 7 changes the Home experience from a dashboard styled like macOS into a desktop host for the existing Livenza applications. Backend routes, authentication, permissions, database workflows and integrations remain authoritative; the desktop shell opens eligible same-origin application routes inside managed windows and falls back to normal full-page navigation when a route cannot be safely mounted.

### Desktop and Window Behaviour
- Functional-only Dock registry: apps appear only when their route exists, the signed-in user is permitted to use them, and required provider capability is available.
- One managed window per application endpoint with focus/z-order, pointer-captured drag, resize, minimise, restore, zoom/maximise, close, direct full-page fallback and session geometry persistence.
- Contextual menu bar: decorative `Edit`/`Go` items are removed; `File` exists only with an active app window, while `View` and `Window` expose implemented commands only.
- Same-origin mounted pages load their required styles, external scripts and trusted inline application scripts, then reuse `LivenzaInitPage` so existing forms and interactions continue to initialise inside desktop windows.
- Cross-application links can transfer into the matching running Dock application instead of needlessly replacing the desktop.

### Wallpaper and Visual Refinement
- System Settings includes built-in wallpaper previews plus custom image upload, reset and persistent selection.
- The **Livenza.life · LIVE ELEVATED.** scenic wallpaper is the first-run/reset default and is applied before first paint to avoid reload flashing; Aurora and the other built-ins remain selectable, while custom images are resized/compressed client-side before local persistence.
- Exact supplied-kit shell geometry remains authoritative: 34px menu bar, 58px Dock, 36px Dock icons, 45px stride, 4px running dots, 16px windows, 40/52/77px toolbars, 256px sidebars, 344px widgets and 13/16 desktop body typography.
- Legacy decorative card streaks, floating-card hover effects, hidden Home toolbar DOM and the old footer safe-area reservation are removed from the clean shell.
- Form controls, labels and buttons use a consistent baseline/alignment contract; primary application content remains high-contrast while Liquid Glass is limited to navigation/transient surfaces.

### Motion and Performance
- Dock proximity magnification is requestAnimationFrame-throttled and keeps running indicators fixed.
- Window opening/closing/minimise motion uses restrained spatial scale/opacity rather than large generic zooms, with complete Reduced Motion fallbacks.
- Home reuses the shared companion pulse instead of polling the same endpoint twice; idle/ambient Home timers are reduced and hidden-tab work is paused where applicable.
- Retired theme/shell layers are no longer loaded by `base.html`; the clean shell uses one authoritative macOS system layer over the retained module compatibility sheet.
- Full-viewport backdrop blur and body-wide brightness filtering are avoided to reduce Chromium compositing cost.

### Hotfix 7 Verification Scope
The packaged source is verified with Python contract tests, Python compilation, JavaScript syntax checks, all Jinja templates parsed, and a real Chromium/Playwright shell fixture at 1440×900 and 1152×720. The Chromium audit checks exact geometry, no page overflow, widget/Dock separation, representative text overflow, wallpaper rendering, Dock magnification, window open/focus/drag/resize/minimise/restore/maximise/close, contextual menus, inline mounted-page script execution and Reduced Motion behaviour. The final browser audit is required to pass twice consecutively after the last code change.

The sandbox used to prepare this package does not have Flask installed and cannot open an authenticated live `backoffice.livenza.life` session. Therefore the Chromium verification is a deterministic browser fixture of the production shell code, not a claim that the live deployment itself was remotely exercised. Run `VERIFY_DEPLOY.txt` after deploying the ZIP to validate the real environment and provider-backed workflows.

## Hotfix 8 — macOS 27 Suite Polish

Hotfix 8 keeps the Hotfix 7 browser-OS architecture and refines the functional application windows themselves. Each major Livenza suite now receives a restrained but recognizable visual family, unique Dock artwork, improved sub-window typography/alignment and macOS-style motion while preserving the existing backend, route, permission and integration behavior.

### Application visual identities
- Agreements use a blue/indigo productivity treatment; Rooms/Residents use cyan/teal occupancy cues; Queries use orange pipeline cues; Reviews use yellow/pink reputation cues.
- Video Wall and Letterhead use creative pink/violet identities; Food uses green/orange hospitality accents; Billing/Banking use teal/navy finance treatments; Electricity uses amber/orange utilities cues.
- WhatsApp/Email/Drive use communication/document accents, while Settings/Admin surfaces remain calmer violet/graphite system surfaces.
- Colour is concentrated in Dock artwork, suite title chrome, selected states, status chips, data highlights and restrained canvas washes instead of flooding whole working surfaces.

### Alignment, motion and graphics
- Functional Dock icons use application-specific SVG symbols; blank/generic placeholder artwork is rejected by the Hotfix 8 contracts and browser audit.
- Finance/stat values use non-wrapping tabular numerals, table/card treatments inherit the active suite family, and the Home date line box was adjusted after Chromium clipping detection.
- Suite-content materialization, card/tab interaction and titlebar accent motion remain brief and fully suppressed by Reduced Motion.
- Eight original built-in wallpapers are available alongside custom wallpaper: Aurora, Spectrum, Sequoia, Midnight, Livenza Blue, Violet Glass, Ocean and Sunrise.

### Performance refinement
- The legacy footer clock no longer runs an unconditional 1-second interval while hidden.
- Video Wall state and heartbeat loops are visibility-aware and pause when the player page is hidden.
- Retired historical presentation assets remain removed rather than reintroduced as another Hotfix stylesheet.

### Hotfix 8 verification scope
The exact packaged source is verified with 26 Hotfix 8 contract tests, Python compilation, JavaScript syntax checks, all 73 Jinja templates parsed, and a 24-scenario Chromium/Playwright audit across 1920×1080, 1440×900, 1366×768 and 1152×720. The browser audit covers representative Agreements, Banking, Creative/Letterhead, Settings, overlapping-window and Reduced Motion states and must pass twice consecutively after the final production-code change. See `HOTFIX8_AUDIT.md` for the complete record and environment limitation.

## Hotfix 9 — Precision UI/UX + Single Window Design System

Hotfix 9 standardizes the application suites around one shared Tesla OS window language. Agreements is the structural baseline and Banking, Rooms, Queries, Reviews, Billing, Electricity, Food, WhatsApp, Email, Drive, Letterhead and Settings now inherit the same route titlebar, typography hierarchy, spacing rhythm, action placement, tabs, cards, forms and tables while retaining distinct Livenza accent identities.

The Suites launcher is redesigned as a light Liquid-Glass-style application browser with compact aligned category controls, meaningful app artwork, professional card widths and normal word wrapping. Direct application routes use a compact 52px window-style toolbar and no longer show a second desktop Dock or duplicate mascot/footer chrome.

Hotfix 9 verification includes 27 dedicated source contracts, the 26 Hotfix 8 regression contracts, Python compilation, all 73 Jinja templates, 8 production JavaScript syntax checks, a 48-scenario multi-resolution Chromium shell audit and a 26-scenario Chromium audit rendering the actual Livenza suite templates. See `HOTFIX9_AUDIT.md` for the exact scope and environment limitation.

## Hotfix 9.1 — Marquee-Free Vibrant Suite Refinement

Hotfix 9.1 removes the legacy operational marquee/status strip completely from the browser UI, Settings, client polling and runtime route context. The removed strip no longer consumes hidden vertical space, influences drawer geometry or runs a periodic market/status request.

The normal Tesla OS application experience is now explicitly bright and colourful by default rather than following a dark Windows/browser colour scheme. Dark appearance remains available only when deliberately selected and uses layered graphite surfaces instead of near-black slabs. Suite content retains the shared Hotfix 9 window, typography, cards, forms, tables and toolbar system while strengthening application colour identity. Electricity receives a dedicated amber/orange/mint utility treatment and the other suite families gain richer tertiary accent materials without changing their professional content hierarchy.

Verification for this pass is recorded in `HOTFIX91_AUDIT.md`.

## Hotfix 9.2 — Bright Settings + Persistent Interactive Dock

Hotfix 9.2 continues the approved macOS-style refinement specifically around System Settings and the global Dock. It introduces a new `livenza.settings.v2702` preference namespace so stale appearance values from older builds cannot unexpectedly reopen the new interface in a dark/purple state. Older non-appearance preferences continue to migrate, while the Hotfix 9.2 experience starts bright by default; Dark remains an explicit user choice after that migration.

The Dock is restored as a persistent signed-in navigation surface on direct application routes, with route content reserving a proper bottom safe area so long pages cannot scroll beneath it. Dock size, magnification and auto-hide changes therefore have an immediately visible target while the user is in System Settings. Proximity magnification now combines scale with a restrained 13px vertical lift, and switching magnification off clears any active transform immediately.

The focused Chromium Settings render confirms a bright application canvas, bright Settings detail/card surfaces and a visible 58px Dock. Source verification and deployment notes are recorded in `HOTFIX92_AUDIT.md` and `VERIFY_DEPLOY.txt`.


## Hotfix 10 — Lightweight Shell, Brand System & Deployment Cache Fix

Hotfix 10 continues from Hotfix 9.2 but removes the largest source of perceived lag on the desktop itself: Home no longer boots the ~304 KB legacy module stylesheet, ~101 KB general app runtime, TV compatibility layer or ~129 KB macOS application stylesheet. Home instead uses `home_light.css` and `home_light.js`; System Settings uses `settings_light.css` and avoids the legacy module/app/TV bundles. Heavy suite code remains available only where the corresponding suite actually needs it.

### Deployment cache correction
Static files are deliberately served with a long immutable cache lifetime. Earlier hotfixes kept `?v=27.0.1`, which allowed a browser or CDN to reuse older CSS/JS even after a newer ZIP was uploaded. Hotfix 10 fixes the source rather than relying on users to clear cache: versioned static URLs now carry **`?rev=27A101-H10L-20260827D`**, `/version` reports that revision, and responses expose `X-Livenza-Revision` / `X-Livenza-Hotfix`. The default scenic wallpaper also uses revision-specific `livenza_life_live_elevated_h10l.jpg`.

### Visible Home contract
- Livenza.life scenic wallpaper is first-run/reset default.
- New Livenza wordmark in the menu bar.
- Seven curated Dock shortcuts: Suites, Agreement Studio, Rooms, Queries, Reviews, Banking and System Settings, respecting permissions where applicable.
- Widgets are hidden until requested.
- Livenza Companion sits above the Dock at the lower-right; its panel opens on demand.
- View/Suites/Search interactions are local lightweight operations with no network dependency before opening.
- Dock proximity motion uses requestAnimationFrame/GPU transforms and respects Reduced Motion.

### Refined lightweight System Settings
System Settings renders a bright macOS-style sidebar/detail surface without inherited purple/black slabs. Desktop & Dock now visibly separates Dock Size from Magnification and Auto-Hide switch rows; the same lightweight layer defines form grids, switches, wallpaper cards, range/value rows, action controls and responsive behavior so the real Jinja templates do not collapse into browser-default flow.

### Livenza identity
The approved three-logo package remains authoritative: `livenza_wordmark_tagline.png` for formal/authentication/document contexts, `livenza_wordmark.png` for horizontal UI identity and `livenza_life_mark.png` for compact system/PWA/favicon contexts. Agreement and Letterhead PDF defaults use the approved lockup while retaining custom Letterhead-logo override behavior.

### Runtime reliability retained
Hotfix 10 retains the 8-second application timeout with Retry, wallpaper fit/position/zoom, window Zoom/Restore, contextual history controls where used, non-interactive wallpaper layers and protected backend/role behavior.

### Verification
The exact release tree is verified with the complete source regression suite, Python compilation, all production JavaScript syntax checks, all Jinja templates, CSS structure checks and focused Chromium audits. The Home audit covers 1920×1080 and 1366×768, verifies seven Dock items, widgets asleep on load, immediate View-menu execution, lower-right Companion and no horizontal overflow. The Settings audit verifies bright geometry/no overflow, and the actual `system_settings.html` Desktop & Dock template is rendered separately to confirm properly separated controls and switches. Live production verification remains a separate deployment step using the revision fingerprint in `VERIFY_DEPLOY.txt`.


### Hotfix 10 deployment-survival hardening — revision B
Revision `27A101-H10L-20260827D` additionally cache-busts every browser-visible static asset referenced from Jinja templates. Unversioned `/static/*` requests now revalidate instead of receiving a one-year immutable cache header. PWA icons and the CSS-embedded compact Livenza mark use Hotfix-specific filenames. This prevents a correct server deployment from still looking like the prior release because a browser/CDN retained an older logo, favicon, icon or image URL.

## Livenza.life V1 consumer foundation

The consumer-facing Livenza.life platform uses a separate passwordless customer identity from the existing staff `User` login. The V1 API prefix is `/api/v1`; the existing back-office login and permission model remain unchanged.

### Customer authentication environment

```text
CUSTOMER_AUTH_TEST_MODE=0        # 1 only in local/test; never production
CUSTOMER_SESSION_DAYS=30         # customer session lifetime
CUSTOMER_OTP_EXPIRY_MINUTES=5    # OTP validity
CUSTOMER_OTP_MAX_REQUESTS_15M=5  # identifier rate window
```

`CUSTOMER_AUTH_TEST_MODE=1` only returns a test OTP when `LIVENZA_ENV`, `FLASK_ENV`, or `ENVIRONMENT` explicitly identifies a local/development/test environment. A production or unspecified environment never exposes the OTP in an API response.

### Foundation migration order

1. Back up the staging PostgreSQL database.
2. Apply `migrations/livenza_v1_foundation.sql` to staging before any consumer frontend or Plan 2 traffic is connected.
3. Start the back-office against staging and verify existing staff login, permissions, integrations, rooms, tenants, and core suites.
4. Smoke-test `/api/v1/cities`, `/api/v1/properties`, customer OTP delivery, verification, logout, and `/api/v1/me` on staging.
5. Only after staging passes should the same additive migration be applied to production before enabling consumer traffic.

The migration is additive and does not drop, rename, or alter the legacy `user`, `room`, or `tenant` tables.

## Livenza.life consumer web — Plan 2

The customer-facing Livenza.life experience now lives in `web/` as a separate Next.js App Router application. It consumes the versioned Flask API added in Plan 1 instead of accessing back-office database tables directly.

Required consumer deployment variables:

- `LIVENZA_API_ORIGIN` — server/API origin used for Next.js `/api/*` rewrites and server-side property discovery.
- `LIVENZA_SITE_URL` — canonical consumer origin used by sitemap and metadata helpers.

The Plan 2 checkpoint includes the master brand homepage, `livenza.stays` search/city/property discovery, future-vertical early-access pages, safe Store/My Livenza/booking handoffs, SEO/analytics contracts, and Playwright/bundle guardrails. Plan 3 replaces the booking handoff with live inventory holds, customer identity, payments, and My Livenza transactions.

Production verification still requires Node.js 20.9+ with the dependencies in `web/package.json`, then `npm test -- --run`, `npm run lint`, `npm run build`, `npm run check:bundle`, and `npm run test:e2e`.

## Livenza.life V1 booking, payments and My Livenza — Plan 3

Plan 3 replaces the consumer booking handoff with the live transaction layer. The Flask API now owns timed inventory holds, Book Now/Reserve bookings, server-priced add-ons, parent-share tokens, Razorpay order creation, signed webhook confirmation, printable receipts, and owner-scoped My Livenza data. The Next.js application contains the OTP sign-in and booking wizard, parent-share continuation, payment/confirmation views, and My Livenza dashboard modules.

### Booking/payment deployment variables

- `RAZORPAY_KEY_ID` — public checkout key returned to the consumer only when payment starts.
- `RAZORPAY_KEY_SECRET` — server-only Razorpay API credential.
- `RAZORPAY_WEBHOOK_SECRET` — server-only HMAC secret used against the raw webhook request body.
- `RAZORPAY_TEST_STUB=1` — permitted only in local/development/test environments; creates local order IDs while preserving the webhook confirmation path.
- `BOOKING_ADDONS_JSON` — server-authoritative add-on catalog. Client-supplied prices are ignored/rejected; only configured codes can be booked.
- `PARENT_SHARE_EXPIRY_HOURS` — parent-share validity, default 24 hours.

### Plan 3 migration and staging order

1. Back up staging PostgreSQL.
2. Ensure `migrations/livenza_v1_foundation.sql` is already applied.
3. Apply `migrations/livenza_v1_booking_payments.sql` to staging. It is additive and contains no table/column drops.
4. Seed at least one public property, room category, allocatable inventory unit, and `stay_rate_plan` before testing booking.
5. Configure customer OTP delivery and Razorpay Test Mode credentials/webhook secret on staging.
6. Configure the Razorpay webhook target as `https://<api-host>/api/v1/payments/webhooks/razorpay` and enable the payment/order events required by the gateway account.
7. Verify Book Now and Reserve separately. Browser checkout success is not confirmation; the booking must remain pending until the signed webhook marks the payment paid.
8. Verify duplicate webhook delivery leaves one processed event and one booking confirmation.
9. Verify failed payment never confirms inventory, expired holds cannot start payment, and a second customer cannot see another customer's booking, receipt, payment, document, or support record.
10. Verify parent-share expiry and login/payment continuation with no resident KYC/private documents exposed.
11. Run the mobile and desktop booking Playwright journey against staging PostgreSQL before production migration.

### Consumer checks

From `web/` with Node.js 20.9+ and dependencies installed:

```text
npm test -- --run
npm run lint
npm run build
npm run check:bundle
npm run test:e2e -- booking.spec.ts
```

The E2E booking spec expects a staging fixture through `E2E_PROPERTY_SLUG`, `E2E_ROOM_CATEGORY_SLUG`, `E2E_CUSTOMER_MOBILE`, `CUSTOMER_AUTH_TEST_MODE=1`, `RAZORPAY_TEST_STUB=1`, and a test `RAZORPAY_WEBHOOK_SECRET`. The test stubs only the external Razorpay popup; confirmation still goes through the signed webhook endpoint.
