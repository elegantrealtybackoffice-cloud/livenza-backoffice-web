# Livenza Life Operations Cloud — Web 1.9.0





## Web 1.9.0 Maintenance — Liquid Glass UI, iMac/5K & Live Mascot

- Introduces one site-wide **Livenza Liquid Glass** material system with deep navy/blue/violet wallpaper, translucent layered surfaces, white compact system typography and consistent active/inactive icon states.
- Adds an original Livenza abstract wallpaper asset (`static/livenza_liquid_wallpaper.webp`) with a lighter low-capability rendering path; no Apple artwork, marks or proprietary icon assets are included.
- Completes a 52-template text-fit audit: important labels, headings, cards, forms and vault values wrap and grow naturally instead of relying on ellipsis or hidden overflow.
- Verifies responsive geometry from **390×844 through 5120×2880**, including 2560×1440, 2880×1800 and 3200×1800 iMac/large-monitor layouts. Large screens use a bounded 2160px content canvas and additional application-grid columns instead of oversized cards or excessively long text lines.
- Keeps the original blue robot **persistently available across authenticated pages** when enabled. Lightweight idle motion remains active in mobile/low-capability/TV performance modes unless the operating system explicitly requests reduced motion.
- Live mascot operations refresh every two minutes, pause while the page is hidden, resume on return, recover immediately after browser online/back-forward page restoration, retain the last safe state during network failures and visually react when safe operational summary values change.
- Restores the blue robot to the login welcome experience and removes visible “3D host” labeling from current mascot settings. Compatibility setting keys remain internal so existing deployments do not require a migration.
- Replaces primary grouped-navigation glyphs with custom `currentColor` SVG geometry and synchronizes selected/pressed/on/off state styling for Liquid Glass controls.
- No database migration is required for this visual/interaction maintenance layer.

## Web 1.9.0 Maintenance — Motion, Marquee & Text Reliability

- Decouples ordinary UI capability from WebGL availability so missing WebGL no longer disables the lightweight blue-robot mascot or general interface motion.
- Restores the blue robot, live operations marquee and lightweight card/reveal transitions in normal motion mode, including mobile/low-capability performance profiles.
- Rebuilds the live marquee as a measured two-group seamless loop that restarts after live-data refresh and resizes without duplicated static rows.
- Makes shared text-bearing cards, page heads, forms and status surfaces content-driven so wrapped copy grows vertically instead of being clipped or hidden.
- Removes unsafe `content-visibility`/paint-containment optimizations from text-heavy UI while retaining clipping only for explicit media, masks and local scrolling surfaces.
- Keeps `prefers-reduced-motion` authoritative: users who explicitly request reduced motion receive static mascot/marquee behavior with readable local marquee scrolling.
- No database migration is required for this maintenance update.

## Web 1.9.0 Maintenance — Blue Robot & Grouped UI

- Restores the original blue Livenza robot as the default live mascot and removes the WebGL 3D host runtime from the default page shell.
- Rebuilds Mascot Settings with responsive native controls while preserving existing preference compatibility and Admin policy keys.
- Replaces the long hamburger application list with categorized tabs and a responsive application grid.
- Uses the same shared application catalog on Home and in the three-line menu, including **Livenza Letterhead Studio** from Web 1.9.0.
- Adds site-wide text wrapping, touch-target, translucent mascot-chat, reduced-motion and low-capability performance hardening.
- No database migration is required for this maintenance update.

## Web 1.9.0 — Livenza Letterhead Studio

### Web 1.9.0 highlights
- Adds **Livenza Letterhead Studio** with Ask Livenza AI, manual/hybrid drafting, Final Review, controlled PDF issuance and a searchable automatic Document Vault.
- Adds connected, permission-aware internal-data drafting with sensitive-data minimization and explicit user approval before protected supporting documents are attached.
- Adds user-authored letterhead template drafts with Admin-only publication, immutable published versions, protected signatures/seals and versioned template history.
- Adds Email and WhatsApp delivery using providers configured only in the centralized **Integrations Center**, with retryable delivery state/history.
- Adds automatic reference numbering, immutable finalized PDFs, revision chains, audited no-store downloads and encrypted-at-rest Letterhead assets using `LIVENZA_VAULT_MASTER_KEY`.

### Deployment
v1.8.0 must already be deployed/merged. Apply `migrations/web_v1_9_0.sql` where automatic table creation is unavailable. Historical PDFs are not automatically reconstructed into the new Document Vault. See `README_v1.9.0.md` for complete deployment notes.


## Previous platform foundation — Web 1.8.0

Web 1.8.0 introduced the centralized Integrations Center, Vault-backed integration configuration, Smart-TV compatibility bootstrap and responsive layout foundation used by Web 1.9.0. Its experimental WebGL mascot presentation is superseded by the **Web 1.9.0 Blue Robot & Grouped UI maintenance** above; the blue Livenza robot is the current default mascot.

## Web 1.7.1 — Glass Applications Drawer + Landlord/Tenant Masters

### Web 1.7.1 highlights
- Replaces the oversized Applications mega-menu with a **left-side translucent glass drawer**. The drawer keeps application icons opaque and legible, preserves permission-aware navigation, supports outside-click/Escape dismissal and adapts to mobile width.
- Adds separate **Landlord Master** and **Tenant Master** workspaces with searchable reusable records for identity, contact, address, corporate/tax, banking/refund, foreign-national/compliance and operational metadata.
- Adds **encrypted master documents** for Aadhaar/PAN/passport/visa/authorization/company/bank-proof and other approved attachments. Documents use AES-GCM with `LIVENZA_VAULT_MASTER_KEY`, generated storage identifiers, immutable replacement history and Admin re-authenticated downloads.
- Sensitive identity and financial fields are **masked by default**. Admin password re-authentication is required for temporary reveal; raw sensitive values are excluded from audit metadata and ordinary search text.
- Agreement Studio can select a saved landlord/tenant master and **fill empty agreement fields without overwriting existing values**. Replacing values requires an explicit action. Agreement edits never silently update a master.
- Admins can explicitly create/update masters from Agreement Studio and select master documents as **protected agreement annexures**. PDF/image annexures are embedded in the protected combined PDF; unsupported document formats remain protected references.
- Existing encrypted `AgreementPartyProfile` records are migrated idempotently into the appropriate master while the legacy table is retained for rollback compatibility.
- Non-admin Agreement users can use safe master summaries for drafting but cannot edit, reveal, upload/download protected documents, archive, duplicate or mutate sensitive master data.

### Required production secret
Set and keep `LIVENZA_VAULT_MASTER_KEY` stable in Render/production before creating or migrating protected master data. If this key is missing, protected master creation/migration/document encryption must not be treated as operational. Never commit the key to GitHub.

### Deployment verification
- Application version marker: **Web 1.7.1**
- Apply `migrations/web_v1_7_1.sql` when your managed PostgreSQL/Supabase role does not permit automatic table creation.
- After deployment, open `/version` and confirm `Web 1.7.1` plus `left-glass-app-drawer`, `landlord-master`, `tenant-master`, `encrypted-master-documents`, `agreement-master-autofill`, and `agreement-master-annexures`.

---

## Previous release — Web 1.7.0
## Web 1.7.0 — Electricity Bill Studio, Livenza Vault, Live Reminders & AI Mascots


### Web 1.7.0 highlights
- **Electricity Bill Studio** with a seeded pan-India provider directory (73 provider/coverage entries across 37 state/UT labels).
- Save city/property electricity connections with K No., CA No., Consumer No., Account No., service/meter identifiers and due-reminder preferences.
- Authorized Bharat Connect / BBPS-ready bill-fetch adapter with truthful official-portal/upload fallback when provider integration is not configured.
- Secure uploaded-bill storage, PDF/image/spreadsheet extraction, month-wise Electricity Bill Register, CSV and Excel export.
- **Live Reminders** on the home dashboard for due-soon, due-today, overdue and payment-pending electricity bills.
- Admin-only **Livenza Vault** for encrypted electricity logins and operational API/payment secrets; Vault explicitly rejects bank passwords, UPI/card PINs, CVV, OTP, CAPTCHA and banking session cookies.
- Admin-controlled electricity provider overrides, audit trail and protected payment confirmation.
- Live mascot correction: uploaded photos remain profile/source images; the workspace mascot is an AI-stylized character or the standard Livenza mascot, never a plain photo fallback.

This is the current Livenza Life Operations Cloud release.

### What changed

- **Avatar Studio reliability:** direct webcam-blob submission, laptop camera diagnostics, camera selection/retry, phone camera picker, broader photo intake and a server-side polished-avatar fallback.
- **Banking Suite:** searchable bank dropdown and secure launchers for official bank websites, using current official destinations where verified.
- **Statement Vault:** save bank statements inside Livenza after explicit upload, with encrypted storage for supported deployments.
- **Bank Reconciliation:** upload reusable templates and compare bank-statement entries by amount, date, reference/UTR and narration; review matched, missing, extra and exception entries; export reconciliation results.
- **Full Screen restored:** the header full-screen control remains available and internal Livenza navigation is handled in-place wherever browser security permits.
- **360° lifestyle identity:** the sitewide visual direction represents Livenza Life as a broader lifestyle/operations ecosystem rather than only hotel rooms.

### Deployment

- Application version marker: **Web 1.7.0**
- Runtime: **Python / Flask**
- Deploy with the supplied `Dockerfile`, `render.yaml` or another compatible Python hosting service.
- **GitHub Pages alone cannot run the Flask routes** used by Avatar Studio, Banking, reconciliation, login and other server features.
- After deployment, open `/version` and confirm the response reports `Web 1.7.0`.

### Security notes

Livenza does not proxy or store bank passwords, PINs, OTPs, cookies or authenticated bank sessions. Bank sites that disallow iframe embedding must open through their official secure site. Browser security also prevents a normal website from silently reading the computer's Downloads folder, so downloaded statements must be explicitly selected for upload.

---

## Previous release history

# Livenza Life Operations Cloud — Web 1.5.13

## Web 1.6.2 admin-managed mascots, profile lock and permissions

- The initial sign-in card now shows only Login ID and a clearly separated **Verify Device** action, with Windows Hello, Touch ID, Face ID and passkey support shown as secondary text.
- Password and gesture entry remain hidden until device verification fails or the user opens **Try another sign-in method**. The fallback uses accessible Password and Gesture/Keypad tabs so the two methods never compete on screen.
- Password Login has a distinct **Biometric-free option** status badge, a visibility toggle and field-specific live error guidance.
- Touch devices retain smooth gesture drawing. Fine-pointer desktop devices receive a numbered 3×3 keypad that accepts number keys 1–9, Backspace and Delete without slow arrow-key navigation.
- Four live progress nodes show pattern completion and turn green when the four-point minimum is reached. A visible SVG **Clear Pattern** action replaces the old double-tap interaction.
- Text-symbol interface icons in the authentication and primary navigation surfaces were replaced with scalable inline SVG icons.
- The legal/company disclosure remains outside the sign-in card in a muted utility footer.
- Rotation Lock, Horizontal and Vertical are now consolidated into one compact **Display** dropdown immediately beside the three-line Applications button. The old floating Home controls and extra rotation items are removed.

No new database migration is required. Existing installations upgrading from before Web 1.5.12 must still apply `migrations/web_v1_5_12.sql`.

## Web 1.5.12 personal live avatar and rotation stability

- A profile-photo upload now creates a clean personal companion avatar and applies it to login welcomes, live updates, weather, help and the account identity.
- The Avatar Studio provides automatic upload progress, a responsive preview, regeneration and a one-click return to the original Livenza mascot.
- When `OPENAI_API_KEY` is configured, the app uses the current GPT Image edit workflow for an identity-preserving professional avatar. A private polished portrait fallback keeps the feature functional if the image service is unavailable.
- Website rotation now applies instantly without waiting on native orientation APIs, deduplicates resize/orientation work and suspends costly full-page effects while rotated.
- The Rotate menu is outside the transformed workspace so users can always reopen it and return to Automatic mode.
- Home now includes direct icon controls for rotation lock, Horizontal and Vertical modes, with persistent active states.
- Apply `migrations/web_v1_5_12.sql` on managed PostgreSQL/Supabase databases. SQLite/local installations add the columns automatically at startup.

## Web 1.5.11 restored website rotation

- The **Rotate** control is restored directly in the authenticated top header.
- Its responsive popover provides Automatic, Portrait, Landscape, 90°, 180° and 270° website modes plus Full Screen / safe theatre mode.
- The selected mode is retained on the device and reapplied across in-place navigation and fullscreen changes.
- The menu supports Escape dismissal, outside-click dismissal and Arrow/Home/End keyboard navigation.
- On compact scrolled headers the control hides with the other right-side actions, preserving the small hamburger-and-logo layout.

No database migration is required.

## Web 1.5.10 progressive secure access

- Login is now one central card with a dominant Login ID field and **Continue with Device Security** action. Pressing Enter from the primary field follows the same WebAuthn flow.
- A lightweight skeleton state appears while Livenza checks local device credentials and waits for the native Windows Hello, Touch ID, Face ID or passkey prompt.
- Password and gesture options are hidden on the initial screen and revealed through one accessible **⚙️ Try another sign-in method** control.
- Password fields include a keyboard-accessible eye toggle. Login failures now return field-specific inline guidance for missing details, Caps Lock, password mismatch, incomplete patterns and inactive accounts.
- Gesture entry uses large numbered targets, pointer/touch drawing, roving keyboard focus, Arrow/Home/End navigation, Enter/Space selection, `aria-pressed` state, a live selection count and a visible **🧹 Clear Grid** button. Double-tap clearing has been removed.
- Legal and administrative metadata now lives in a muted absolute bottom strip, separated from authentication actions. Form frames and confirmation selectors have hover, focus and pressed feedback.

### Web 1.5.10 deployment

No database migration is required. Confirm `/version` returns `Web 1.5.10` and reports `progressive-device-auth`, `password-visibility-toggle`, `keyboard-pattern-navigation` and `absolute-legal-strip`.

## Web 1.5.9 unified mascot assistant

- The separate footer chatbot has been removed. The persistent mascot is now the single entry point for both live information and workspace help.
- The mascot panel has accessible **Live** and **Ask Livenza** tabs. Help suggestions and typed questions continue to use the secure same-origin help endpoint.
- One close control and Escape close the entire companion; focus returns to the mascot trigger.
- The mascot artwork is now a high-fidelity transparent cutout with clean antenna, cap and body edges, a restrained glow, soft grounding shadow and subtle idle motion. No rectangular artwork background remains.
- Existing non-blocking placement, scroll collapse and the sub-400 px minimalist bubble are preserved.

### Web 1.5.9 deployment

Deploy as usual, then confirm `/version` returns `Web 1.5.9` and includes `unified-mascot-assistant`, `standalone-chatbot-removed` and `transparent-polished-mascot`. No database migration is required for this release.

## Web 1.5.8 secure workflow and reliability release

- Aadhaar uploads now use bounded server OCR with Tesseract plus RapidOCR fallback, a 100-second browser timeout, JSON-safe errors and exact reader diagnostics. The Docker deployment installs the required OCR binary; the document is not retained.
- Video Wall media uses signed resumable browser-to-storage uploads in 6 MB pieces. A finished object is verified before its database record is created, progress is visible, and uploaded MP4/M4V/WebM/MOV media appears immediately in Available Media.
- Agreement Studio is a four-step wizard with visual presets, local auto-save status, inline explanations, branded legal-workspace artwork, a protected-workspace disclosure and WCAG-focused controls.
- Landlord and tenant party profiles can be saved and applied in one click. Profile payloads are encrypted at rest with `INTEGRATION_ENCRYPTION_KEY` (or the derived deployment key).
- Query Sheet opens with 30 editable blank rows, supports tabular paste, existing-row auto-save, multi-row Save All, 10-row expansion and direct `.xlsx` / `.csv` import.
- Login is biometric/passkey first with password and a fluid pointer/touch gesture matrix as fallbacks.
- The ordinary portal now relies on native responsive CSS instead of a global manual fullscreen/orientation menu. Per-TV installed rotation remains in Video Wall Studio where it belongs.
- The mascot docks bottom-left, never intercepts underlying gestures, collapses to a small translucent bubble on scroll and becomes bubble-only below 400 px. Main content reserves 80 px of safe bottom space.
- The header L remains entirely inside the compact translucent header, uses two restrained orbiting light points, and no longer collides with the LIVE marquee. Low-priority signed-in ticker text is hidden on narrow phones.

### Web 1.5.8 deployment

1. Deploy with the supplied `Dockerfile` / `render.yaml`; this installs Tesseract and runs one threaded worker for predictable OCR memory use.
2. Run `migrations/web_v1_5_8.sql` when the production database role cannot create new tables automatically.
3. Keep `INTEGRATION_ENCRYPTION_KEY` stable so saved party profiles remain decryptable.
4. Configure `SUPABASE_SERVICE_ROLE_KEY`, and ensure the public `video-wall-media` bucket/global file limit matches `VIDEO_WALL_MAX_MB`. Supabase Free projects still enforce a 50 MB object maximum.
5. Confirm `/version` returns `Web 1.5.8`, then test one clear Aadhaar, one MP4 upload, a landlord profile and a three-row Query Sheet batch.

## Web 1.5.7 mascot, logo and display-wall polish

- The persistent mascot is smaller, frameless and docked to the bottom-right so it remains lively without covering page content.
- The rectangular mascot prompt has been removed. Click the character to open the same weather, operations, forecast and motivational update panel.
- The header L stays still with no circular ring, tile or halo; two restrained light dots orbit independently for a cleaner AI accent.
- 90°, 180° and 270° rotation now use measured visual-viewport dimensions and stay active in fullscreen across television, signage and video-wall browsers.
- Fullscreen includes vendor-prefixed browser support and a browser-safe theatre fallback when a television browser blocks the Fullscreen API.
- No database migration is required.

## Web 1.5.6 Aadhaar, header and mobile reliability

- Agreement Aadhaar uploads now use bundled server-side OCR automatically, with direct PDF text extraction and optional secure AI enhancement. The phone or Windows device does not need an AI/OCR setup.
- The L logo and its AI light effect now sit fully inside the header and never cover the LIVE marquee.
- Scrolling contracts the header to the applications button and a small centred L avatar; account and admin destinations remain available inside the applications menu.
- Phones and constrained devices receive a preloaded performance mode that removes expensive blur, shimmer, tilt and background-particle work while preserving content, the mascot panel and lightweight temporary weather.
- No database migration is required. Deploy the updated OCR dependencies from `requirements.txt`.

## Web 1.5.5 Livenza Live Companion

- The welcome mascot now remains at the side of every authenticated page after its login dance instead of disappearing permanently.
- It performs short, spaced-out playful actions and uses floating generative stars inspired by the supplied Squarespace Design Intelligence reference.
- Clicking the mascot opens a compact glass panel with live weather, a four-day forecast, Gurugram/Jaipur/Delhi/Mumbai/Bengaluru switching, current tenant/vacancy/earning/query updates and rotating motivational thoughts.
- Live weather uses a cached, fail-soft Open-Meteo forecast. If weather is unavailable, operational updates and quotes continue working.
- Rain, storm, cloud, fog, snow, sunlight and night scenes briefly affect the website, fade automatically and play at most once per three-hour weather window. Users can replay the scene manually.
- Admin Settings can enable or disable the companion, weather, temporary scenes, operations and quotes, choose the default city, and set the scene duration.
- Reduced-motion mode keeps the information panel while suppressing weather particles, floating effects and mascot routines.

## Web 1.5.4 translucent workspace refinement

- The full website now sits over a soft, depth-rich hospitality backdrop with a light translucent treatment inspired by the supplied reference.
- Every major workspace uses a large blurred outer glass shell, while cards, forms, tables, statistics, integrations and working panels use nested opacity levels for clear hierarchy.
- The transparent top header, LIVE marquee, applications menu, account/display menus, assistant, login card and footer now share one consistent glass material system.
- Existing Livenza typography, stationary AI-lit logo, dashboard photography, hover depth, page transitions, contextual ribbons and login mascot animation are preserved.
- Dense data surfaces keep higher contrast, mobile devices receive a lighter blur treatment, and browsers without backdrop-filter support receive an opaque readability fallback.
- Reduced-motion and print preferences continue to suppress decorative motion and glass effects appropriately.

## Web 1.5.3 login welcome mascot

- The supplied blue Livenza mascot appears on the Home dashboard once after every successful login.
- Password, pattern and fingerprint/passkey login paths all set the same one-time welcome trigger.
- The mascot enters, greets the signed-in user by name, performs a short dance with spotlight and sparkle effects, then exits and removes itself automatically.
- Refreshing the Home page does not replay the sequence. Kiosk users see it after the post-login PIN gate is unlocked.
- Escape or the visible close button skips the sequence, and reduced-motion mode uses a quiet fade instead of dancing.

## Web 1.5.2 visual refinement

- The top-header mark now uses a transparent Livenza asset: no white square or circular tile sits behind the L.
- The L itself remains stationary while the independent AI light runner, halo and orbit indicators animate behind it.
- The header starts transparent and becomes a softly blurred, animated glass ribbon as the page scrolls.
- Major workspaces receive compact contextual photography without pushing the primary controls below a large hero.
- Dashboard applications now use photo-led media panels, hover depth, staggered gallery motion and responsive layouts.
- Reduced-motion preferences pause decorative motion while preserving every control and visual.

## Web 1.5.1 header refinement

- The hanging Livenza logo is now completely stable and never rotates.
- An independent conic light runner, pulsing halo and two orbiting AI indicators animate around the stationary logo, matching the AI-style logo treatment on the Home screen.
- Reduced-motion mode keeps the logo stable and pauses the surrounding effects.

## Web 1.5.0 security and cloud workspace

- Windows kiosk package: automatic Edge kiosk launch at sign-in, enable/disable scripts and official Assigned Access setup guidance.
- Server-enforced Livenza PIN/password gate so authenticated routes remain locked until explicitly unlocked.
- Separate WhatsApp, Email and Google Drive tabs with per-user permissions.
- WhatsApp uses Meta's official Cloud API and signed message webhooks; it does not embed or retain WhatsApp Web QR/browser sessions.
- Google Drive and Gmail use one server-side OAuth connection. Refresh tokens are encrypted at rest.
- Pattern login stores only a salted hash. Fingerprint/Windows Hello uses WebAuthn passkeys; biometric data remains on the user's device.
- Configurable live marquee shows current tenants, vacant beds, earnings, user/favourites/custom text and optional cached Moneycontrol quote-page rates.
- White reference header has a three-bar applications menu, a stable AI-lit hanging Livenza logo and icon-based controls.

### Required deployment steps

1. Run `migrations/web_v1_5_0.sql` in Supabase SQL Editor.
2. Deploy the new dependencies from `requirements.txt`.
3. Configure Google OAuth: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `INTEGRATION_ENCRYPTION_KEY`, and optionally `GOOGLE_DRIVE_FOLDER_ID`. Add `https://YOUR-SITE/integrations/google/callback` as an authorized redirect URI.
4. Configure WhatsApp: `WHATSAPP_CLOUD_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_VERIFY_TOKEN`, and `META_APP_SECRET`. Point the Meta messages webhook to `https://YOUR-SITE/webhooks/whatsapp/messages`.
5. Configure passkeys: `WEBAUTHN_RP_ID=YOUR-SITE-HOST` and `WEBAUTHN_ORIGIN=https://YOUR-SITE`.
6. In Admin, connect Google, assign the WhatsApp/Email/Drive permissions, enable pattern or fingerprint access per user, and optionally enable kiosk lock.

See `README_v1.5.13.md`, `README_v1.5.12.md`, `README_v1.5.11.md`, `README_v1.5.10.md`, `README_v1.5.9.md`, `README_v1.5.8.md`, `README_v1.5.7.md`, `README_v1.5.6.md`, `README_v1.5.5.md`, `README_v1.5.4.md`, `README_v1.5.3.md`, `README_v1.5.2.md`, `README_v1.5.1.md`, `README_v1.5.0.md` and `windows-kiosk/README_WINDOWS_KIOSK.md` for full setup.

## Web 1.4.9 addition
- The Livenza Assistant now has a high-contrast cross icon that remains visible after messages are added.
- The chat can also be closed with the Escape key, and keyboard focus returns to the Ask Livenza launcher.
- Food partner websites now use a reliable secure launchpad instead of a blank or blocked iframe.
- Swiggy and Zomato default portal URLs were refreshed to their current official partner-login destinations.

## Web 1.4.8 additions
- Home LIVE/ONLINE disc replaced by the Livenza logo with an animated AI-style light running around its border, orbiting indicators, halo and soft visual sweeps.
- Food Delivery Hub now includes partner Integrations and Live Partner Websites.
- Official Swiggy Restaurant Partner, Zomato Restaurant Partner and Toing web destinations are pre-configured.
- Automatic food-order ingestion supports incoming webhook feeds and approved API endpoints supplied by partners.
- Partner account passwords/OTPs are never stored by Livenza; API secrets stay in Render environment variables.

See `README_v1.4.8.md` for deployment and connector details.

---

# Livenza Back Office Web 1.3

Live web back-office for Livenza Life.

## Web 1.3 additions
- Liquid-glass visual system with responsive glass icons and motion.
- Sixth suite: **Live Queries Manager** for Meta/Facebook, Google, OTA/PMS, Airbnb-approved software feeds, direct and manual enquiries.
- Hot / Live query PDF sheets and CSV exports.
- Query status, heat, score, assignment, follow-up and WhatsApp reply templates.
- Generic live-query webhook, Google lead webhook and Meta lead webhook adapter.
- Optional WhatsApp Cloud API automatic replies when credentials are configured.
- User profile photos stored in the central database as resized data URIs.
- Masked Aadhaar profile fields + provider-ready verification workflow. Full Aadhaar/VID is not persisted by the app.
- Daily vacant-room WhatsApp PDF automation settings and scheduler endpoint.
- GitHub Actions hourly trigger included; add repository secret `VACANT_REPORT_JOB_TOKEN` and the same Render env var.
- Footer: copyright, Livenza Life LLP head-office address, creator, version, live date/time.

## Important Aadhaar note
Production Aadhaar authentication is not a public unauthenticated API. Configure `AADHAAR_AUTH_URL` and `AADHAAR_AUTH_TOKEN` only for an authorized AUA/KUA/Sub-AUA/provider integration. Otherwise use UIDAI Paperless Offline e-KYC / Secure QR verification and record only the verification reference / last 4 digits.

## Query webhooks
- Generic: `POST /webhooks/queries/<source>` with `X-Livenza-Webhook-Token` matching Admin Settings / `QUERY_WEBHOOK_TOKEN`.
- Google lead form: `POST /webhooks/google/leads` (optional `GOOGLE_LEAD_WEBHOOK_SECRET`).
- Meta Lead Ads: `GET/POST /webhooks/meta/leads`; configure `META_VERIFY_TOKEN` and `META_PAGE_ACCESS_TOKEN` to retrieve lead details by leadgen ID.
- Airbnb/OTA: use approved PMS/channel-manager/API access or send normalized events to the generic OTA webhook. Airbnb API access is subject to Airbnb API program approval.

## Automatic vacant-room reports
1. Add Render env vars `WHATSAPP_CLOUD_TOKEN`, `WHATSAPP_PHONE_NUMBER_ID`, `VACANT_REPORT_JOB_TOKEN`.
2. In Back Office > Settings configure recipients and time (IST), then enable the schedule.
3. In GitHub > Settings > Secrets and variables > Actions add `VACANT_REPORT_JOB_TOKEN` matching Render.
4. The included hourly GitHub Action calls `/jobs/vacant-room-report`; the app itself sends only when the configured IST hour is due and once per day.


# Web 1.4 — Video Wall Studio

The seventh suite adds multi-screen signage control. Each TV gets a unique player URL, can run its own media/playlist, rotation (0–359°), fit mode, loop behavior, and mute setting. A Festive Takeover button temporarily pushes one commercial to every enabled TV, after which screens return to their individual content. Player pages heartbeat back to the control panel for ONLINE/OFFLINE status.

## Persistent media uploads

The database tables and the public Supabase bucket `video-wall-media` are already created by `migrations/web_v1_4.sql`. To enable direct file upload from the Back Office, add this Render secret:

- `SUPABASE_SERVICE_ROLE_KEY` — Supabase Project Settings → API keys → service role/secret key. Keep it server-side only.

The app derives the Supabase project reference from `DATABASE_URL`. External/CDN media URLs work even without the service-role key. On the current Supabase Free plan, individual Storage files are limited to 50 MB; use compressed signage videos or external/CDN URLs for larger files.

## TV setup

Open Video Wall Studio, register a screen, copy its unique Player URL, and open that URL in the smart-TV browser, signage mini-PC, Fire TV browser, or attached computer. Keep the page open. Media changes and festive takeover commands are picked up automatically.
### Web 1.9.0 Light Aqua Liquid Glass maintenance
The current v1.9.0 UI maintenance layer uses a high-key aqua background, highly translucent glass surfaces, compact system typography and a full-site text-containment audit while preserving the persistent animated/live-updating blue mascot and all Letterhead Studio workflows. Printable paper surfaces remain intentionally white with dark text.

### Web 1.9.0 Medium Aqua Adaptive Liquid Glass maintenance
The current Web 1.9.0 presentation uses a medium aqua adaptive glass hierarchy: stronger translucent material for navigation/controls, calmer content surfaces, high-contrast segmented selection, a dedicated final theme layer loaded after feature CSS, persistent live blue mascot behavior, and mobile-to-5K text/layout verification. No database or business-workflow migration is required for this UI maintenance update.

### Web 1.9.0 Refractive Liquid Glass v2 maintenance
The final UI layer now separates calm content material from floating functional glass, uses border-light grouped controls and a milky selected-lens state, and preserves full text wrapping, persistent live mascot behavior and mobile-to-5K responsiveness.

## Golden Glass UI Maintenance

The Web 1.9.0 shell now uses the original **Livenza Golden Glass** final material layer: a graphite/charcoal environment with champagne reflections, neutral smoked functional glass, milky selected lenses, calmer content material, thicker readable popovers, and restrained Livenza cool-blue accents. Active icons transition from silver to champagne/cool luminosity with a short settle animation; reduced-motion users receive the final state without animation. The blue mascot, live operational/weather updates, Ask Livenza, marquee, Letterhead Studio, Integrations and all business workflows are unchanged.

Text-bearing controls remain content-driven and must not use optical clipping. Browser regression coverage includes mobile, desktop, iMac-class and 5K viewports.
