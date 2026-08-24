# Livenza Life Operations Cloud — Web 1.5.1

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

See `README_v1.5.1.md`, `README_v1.5.0.md` and `windows-kiosk/README_WINDOWS_KIOSK.md` for full setup.

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
