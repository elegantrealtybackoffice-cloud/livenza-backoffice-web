# Livenza Back Office Web 1.2

Major online-suite upgrade.

## Added / fixed
- Google Review Generator now requires a Google Business review-request link, shows a live QR, opens the Google review page, downloads the QR and copies the draft before opening Google.
- Agreement Studio now exposes the complete desktop data set (122 legal/operational fields plus City), including stamp/e-stamp, notary, witnesses, regulatory, foreign-client, licence and financial fields.
- Material agreement fields are validated before save; corporate and foreign-client presets add additional mandatory fields.
- Agreement presets now change agreement type, policies and the preset-specific legal format profile/clauses.
- Agreement PDF download plus WhatsApp handoff: opens the tenant's saved WhatsApp chat with a signed 7-day PDF download link.
- City master in Admin and city dashboard on Home.
- Separate manager login IDs with per-application access permissions enforced server-side.
- Colourful animated live theme.
- Footer: Created by Rishabh Kothari + live browser date/time.

## Production database
The Supabase production project has already received the v1.2 schema migration. `migrations/web_v1_2.sql` is included for reference/other environments.

## Deploy
Upload/replace the contents of this package in the existing `livenza-backoffice-web` GitHub repository and commit to `main`. Render should automatically redeploy the live application.

### Important WhatsApp note
A normal website cannot silently attach a local PDF into a WhatsApp chat. The web-safe implementation generates the agreement PDF on the server and opens the tenant's WhatsApp chat with a signed, seven-day PDF download link. True automatic document attachment/sending requires approved WhatsApp Business Cloud API credentials.
