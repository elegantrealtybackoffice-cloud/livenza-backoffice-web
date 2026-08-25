# Livenza Life Web 1.6.0

Major reliability and finance-workspace release.

- Avatar Studio now submits webcam captures directly as image blobs instead of relying on fragile file-input assignment.
- Laptop webcam diagnostics, retry, camera-device selection, secure-context guidance, and camera file-picker fallback.
- Reliable server-side polished avatar is used when external AI image generation is not configured or unavailable.
- New Banking & Reconciliation Suite with official bank launcher, current `.bank.in` destinations where verified, encrypted statement/template vault, CSV/XLSX/XLS/PDF imports, reusable templates, entry matching and CSV result export.
- Bank credentials, OTPs, cookies and sessions are never proxied or stored by Livenza. Bank sites that block iframe embedding open through the verified secure launcher.
- Browser security prevents silent access to the Downloads folder; users explicitly choose a downloaded statement to save it into Livenza.
