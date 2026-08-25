# Livenza Web 1.5.14

## 360° lifestyle visual identity
- Replaces the hotel-room-led site background with a futuristic urban lifestyle scene so the product reads as a broader Livenza Life ecosystem rather than a hotel-only platform.
- Keeps the white/translucent glass workspace for readability and adds restrained digital grid/orbit atmosphere.
- The Billing / Rentok / Video Wall contextual ribbon now uses the same 360° lifestyle direction instead of a hotel-room photograph.
- Uses a dedicated locally packaged Livenza 360° lifestyle atmosphere asset; the workspace no longer depends on the hotel-room background.

## Stronger adaptive avatar AI
- Source preprocessing no longer depends on a centred front-facing crop.
- Adds HEIC/HEIF support for common mobile-camera photos through `pillow-heif`.
- Preserves the whole source frame first, improves dark/soft photos, then builds a multi-view reference board with full frame + left/centre/right crops.
- Runtime AI instructions explicitly support side profiles, three-quarter views, full-body/candid/off-centre/slightly unclear images and conservative identity reconstruction.
- Defaults AI avatar quality to `high` (override with `OPENAI_AVATAR_QUALITY`).
- Local polished fallback remains available if cloud AI is unavailable.

## Selfie capture
- Adds Take Selfie to Avatar Studio.
- Desktop HTTPS browsers use webcam preview/capture; mobile can fall back to the device front-camera picker.
- Captured still image joins the same secure avatar upload flow; live webcam video is never uploaded.

No database migration is required. Deploy the package and confirm `/version` reports `Web 1.5.14`.

## Full-screen restored
- Restores a dedicated full-screen icon beside the display/orientation control in the header.
- Uses native browser fullscreen when permitted and theatre-mode fallback otherwise.
- Internal same-origin module navigation is swapped in-place while fullscreen is active, so changing tabs no longer unnecessarily exits the immersive workspace.
- Fullscreen button label/state stays synchronized across native and fallback modes.
