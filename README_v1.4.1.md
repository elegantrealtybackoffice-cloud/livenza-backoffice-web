# Livenza Back Office Web 1.4.1 — Billing + Fullscreen + Rotate

- Renames RentOK Manager to **Livenza Billing Suite** while preserving the underlying RentOK portal integration.
- Adds a one-click **Full Screen** control in the top navigation.
- Adds a **Rotate / View** control: Auto, Portrait, Landscape, 90°, 180° and 270°.
- On supported devices, Portrait/Landscape also attempts the Screen Orientation API while fullscreen.
- CSS fallback rotates/reframes the Livenza website even when browser/OS orientation lock is unavailable.
- View mode is remembered locally in the browser and can be returned to Auto at any time.
