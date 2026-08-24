# Livenza Back Office Web 1.0

Browser-based replacement for the Windows Back Office suite.

## Modules
- Agreement Studio: shared online agreement records, preset-driven formats, English/Hindi preview, browser Print/Save PDF, tenant/room synchronization.
- Room Status & Tenant Master: central room inventory, tariff/security/joining/leaving dates, vacancy status, empty-room PDF.
- Google Review Generator: OpenAI Responses API when OPENAI_API_KEY is configured, with offline fallback. Prompts are restricted to genuine customer-supplied experience details.
- Food Delivery Hub: unified order ledger, settlement data, CSV import and generic authenticated webhooks for partner integrations.
- RentOK Manager: embedded browser panel where permitted, plus guaranteed new-tab fallback.

## Recommended live address
Use `backoffice.livenza.life` for this application. Keep `updates.livenza.life` for legacy desktop updates.

## Local test
1. `python -m venv .venv`
2. Activate it.
3. `pip install -r requirements.txt`
4. Copy `.env.example` values into your environment.
5. Set a strong `ADMIN_PASSWORD`.
6. `python app.py`
7. Open http://localhost:5000

## Render deployment
This package includes `render.yaml`.
1. Put these files in a GitHub repository, for example `livenza-backoffice-web`.
2. In Render, create a Blueprint from that repository.
3. Set the secret `ADMIN_PASSWORD` and optional `OPENAI_API_KEY` when prompted.
4. Render creates the web service and Postgres database.
5. Add `backoffice.livenza.life` as a custom domain in Render.
6. In GoDaddy DNS, add the CNAME value Render gives you for that custom domain.

Every push to the linked GitHub branch auto-deploys the website. No desktop packages are required for browser users.

## Security
- The app is internet-accessible but login-protected.
- Passwords are hashed using Werkzeug's secure password hashing.
- Use a long random SECRET_KEY and strong ADMIN_PASSWORD.
- Keep OPENAI_API_KEY and partner API secrets only in host environment variables, never in GitHub source.
- For real business use, create individual user accounts and role/audit controls before broad staff rollout.

## WhatsApp automation
The Windows build used desktop UI automation. A cloud web server cannot safely automate WhatsApp Desktop. For automatic online PDF delivery, connect an approved WhatsApp Business/Cloud API provider. The web version keeps the empty-room PDF available immediately and is structured for server-side API integration.

## Food platforms
CSV import/manual ledger work immediately. Live Swiggy/Zomato/Toing order feeds depend on partner credentials, approved APIs or webhooks. The `/webhooks/food/<platform>` endpoint accepts normalized partner events when a `food_webhook_token` is configured in Settings.

## Free deployment path (Render + external Postgres)

This package intentionally uses a **Free Render Web Service** and does not create a Render database.
Set `DATABASE_URL` to a persistent external PostgreSQL connection string (recommended: Supabase Free during testing/small internal use).

Why: Render Free PostgreSQL expires after 30 days, so it is not appropriate for tenant/agreement production records. The web service itself can run on Render's Free plan.

### Render Blueprint values
- Service plan: `free`
- `DATABASE_URL`: paste your external PostgreSQL pooled connection string
- `ADMIN_PASSWORD`: choose a strong password
- `OPENAI_API_KEY`: optional; leave blank if you do not want online AI reviews yet

For Supabase, use the **session pooler** connection string for a persistent IPv4-compatible backend.
