Tesla OS 27 — Version 27.0.1 — Build 27A101 — Internal Server Error Hotfix 1

Use this package as a SELF-CONTAINED OVERWRITE update.

Why this hotfix exists
1. The earlier 39-file delta assumed the immediately previous Neutral Light AI release.
   If it was applied over Golden Glass or another earlier v1.9 build, shared templates such as
   _livenza_symbols.html and system_settings.html could be missing and Flask would return HTTP 500.
2. The Home route still ran the retired dashboard's database queries even though Home now contains
   only the AI identity. The Home route is now intentionally lightweight.

Deployment
- Upload/extract ALL files from this archive into the application root and allow overwrite.
- Keep your existing environment variables/secrets and persistent database/instance data.
- Do NOT copy an old templates/ or static/ folder back over this hotfix afterward.
- Restart/redeploy the web service after upload.
- Then open /health and /version. /health should report status=ok and /version should report
  Tesla OS 27, version 27.0.1, build 27A101.

This archive intentionally includes the complete current templates/static runtime so it does not
rely on any intermediate visual release being present first.
