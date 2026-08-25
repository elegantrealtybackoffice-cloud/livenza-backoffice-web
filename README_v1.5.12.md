# Livenza Web 1.5.12

## Personal live avatar

The Account page now includes Livenza Avatar Studio. Selecting a clear JPG, PNG or WebP photo starts the upload automatically, shows a live preview and applies the completed avatar across the header, login welcome, weather companion, operational updates and help assistant.

With `OPENAI_API_KEY` configured, the server uses `OPENAI_AVATAR_MODEL` (default `gpt-image-2`) and `OPENAI_AVATAR_QUALITY` (default `medium`) to create an identity-preserving professional avatar. If the image service is unavailable, a private Livenza-toned portrait is created locally so the mascot still changes immediately.

The user can regenerate the avatar from the saved profile photo or return to the original Livenza robot at any time.

## Rotation hang fix

Rotation modes now update without blocking on the Screen Orientation API. Resize work is frame-throttled, repeated orientation locks are suppressed, and expensive glass/particle effects are suspended only during 90°, 180° or 270° rotation. The rotation popover is rendered outside the transformed workspace so it remains clickable.

The Home screen also shows direct Rotation Lock, Horizontal and Vertical icon buttons. Rotation lock and the selected display mode persist between page loads.

## Database

Run `migrations/web_v1_5_12.sql` on managed PostgreSQL/Supabase installations. Local SQLite installations add the three avatar columns automatically during startup.
