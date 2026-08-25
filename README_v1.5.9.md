# Livenza Back Office Web 1.5.9

Web 1.5.9 consolidates live status and workspace assistance into one polished Livenza mascot.

## What changed

- Removed the independent footer chatbot launcher and panel.
- Added **Live** and **Ask Livenza** tabs inside the mascot companion.
- Preserved help suggestions, chat history during the page session and the existing `/api/help` response flow.
- Kept a single close control, outside-click dismissal and Escape-to-close with focus restoration.
- Replaced the old opaque mascot artwork with a transparent, high-fidelity cutout and refined its small-screen rendering.
- Removed all button tile, border, radius and box-shadow styling surrounding the full mascot. Only a restrained organic glow and grounding shadow remain.
- Preserved safe bottom spacing, pointer-event isolation, scroll collapse and the minimalist chat bubble below 400 px.

## Deployment

No database migration is required. Deploy the updated static assets and templates, clear any edge cache, and confirm `/version` returns `Web 1.5.9`.

## Acceptance test

1. Sign in and confirm only the mascot appears; there is no footer chatbot.
2. Open the mascot and verify Live weather/operations.
3. Select Ask Livenza, use a suggested prompt and send a typed question.
4. Close with the cross and Escape.
5. Scroll beyond 140 px and verify the mascot collapses without covering content.
6. At widths below 400 px, verify only the small circular chat bubble remains.
