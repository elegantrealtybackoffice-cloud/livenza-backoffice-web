Livenza Backoffice Staff Salary boot hotfix

Purpose
- Keeps Staff Salary Studio already present in the latest main app.py.
- Prevents unrelated consumer booking/payment configuration (Cashfree/private storage)
  from blocking backoffice startup.
- Consumer platform stays OFF by default.
- If consumer APIs are needed later, set LIVENZA_CONSUMER_PLATFORM_ENABLED=1 and
  configure Cashfree + Supabase private storage before deploying.

Deploy
1. Copy app.py and livenza_admin_core.py into repository root.
2. Replace the existing two files.
3. Commit: Fix backoffice startup consumer config gate
4. Push origin and let Render auto-deploy.

No database migration is required for this hotfix.
