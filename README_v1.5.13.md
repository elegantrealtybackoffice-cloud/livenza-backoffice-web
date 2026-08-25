# Livenza Web 1.5.13

## Progressive secure access

- Login begins with one Login ID field and one primary **Verify Device** action.
- Compatible device options are rendered as smaller secondary text, eliminating fused labels.
- Password and gesture/keypad methods are hidden until requested or device verification fails.
- Password and gesture/keypad use separate ARIA tabs and panels.
- Password entry includes an accessible visibility toggle, a **Biometric-free option** badge and field-specific feedback.

## Gesture and keypad accessibility

- Touch and pen devices keep drag-based pattern entry.
- Desktop fine-pointer devices show a numbered 3×3 keypad.
- Number keys 1–9 add nodes, Backspace removes the last node, and Delete clears the sequence.
- Four progress nodes update live and turn green after the four-point minimum.
- Clear Pattern is a visible, keyboard-accessible SVG action.

## Header display menu and visual polish

- Rotation Lock, Horizontal and Vertical now live in one dropdown immediately beside the three-line Applications control.
- The floating Home orientation controls and unnecessary rotation menu items are removed.
- Authentication and key navigation symbols use scalable inline SVG artwork.
- Company and creator metadata remains outside the primary form in a subdued utility footer.

## Deployment

No new migration is required for Web 1.5.13. If upgrading from before Web 1.5.12, run `migrations/web_v1_5_12.sql`. Deploy through the supplied Docker configuration and verify `/version` reports `Web 1.5.13`.
