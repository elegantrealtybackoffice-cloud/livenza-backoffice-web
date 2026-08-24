# Livenza Back Office Web 1.5.0

## Windows kiosk and secure lock

- Server-enforced kiosk lock protects every authenticated page with a dedicated PIN or the user's password.
- Admin can enable/disable the lock and download Windows startup scripts.
- `windows-kiosk/` includes automatic Edge kiosk launch at Windows sign-in plus Assigned Access guidance for full Windows restriction.

## WhatsApp workspace

- New permission-controlled WhatsApp tab uses the official WhatsApp Cloud API.
- Supports outbound text messages, inbound messages, delivery status updates and signed Meta webhooks.
- WhatsApp passwords, QR login sessions and browser cookies are not embedded or stored.

## Google Drive and Gmail

- One server-side Google OAuth connection powers separate Drive and Email tabs.
- Refresh tokens are encrypted at rest.
- Drive supports upload, list, open and download, with optional automatic mirroring of Video Wall uploads.
- Gmail supports recent inbox metadata and sending messages inside Livenza.

## Pattern and fingerprint login

- Admin can set/reset a salted login pattern per user.
- Admin can allow fingerprint/passkey enrollment per user and remove registered devices.
- Users enroll Windows Hello, fingerprint or another platform passkey on their own device; biometric data never leaves the authenticator.

## Live marquee and white reference header

- The running bar can show current tenants, vacant-bed capacity, Food net earnings, signed-in user, favourite things and a custom live message.
- Admin controls every marquee item, refresh interval and up to five attributed Moneycontrol stock/index pages from Settings.
- Moneycontrol pages are fetched conservatively, cached for two minutes and fail closed when unavailable; there is no dependency on an undocumented third-party API endpoint.
- The white header now uses a three-bar applications menu, animated hanging Livenza logo and icon-based location, settings, display and profile controls.
- Animated Livenza picture accents are added across section headers while respecting reduced-motion preferences.

## Deploy

1. Run `migrations/web_v1_5_0.sql` in Supabase SQL Editor.
2. Set Google, WhatsApp and WebAuthn environment values described in `README.md` / `render.yaml`.
3. Deploy and verify `/version` returns `Web 1.5.0`.
