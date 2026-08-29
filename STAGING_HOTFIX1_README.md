# Livenza.life Staging Hotfix 1

Fixes the Next.js/Turbopack production-build failure caused by the accidental bare `life {}` selector in `web/src/app/page.module.css`.

The hotfix removes that invalid selector and adds a regression test that rejects bare/global selectors in `*.module.css` files.

Apply this overlay on top of Plan 5 / branch `livenza-life-v1` without deleting any repository files.
