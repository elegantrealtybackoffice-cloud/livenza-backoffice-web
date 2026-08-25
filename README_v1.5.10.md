# Livenza Back Office Web 1.5.10

Web 1.5.10 modernizes the secure portal around a progressive, device-first sign-in flow.

## Primary flow

- A single centred card presents Login ID and one dominant **Continue with Device Security** action.
- The action immediately starts the WebAuthn `navigator.credentials.get()` flow.
- A skeleton status surface bridges the local credential check and native device prompt.
- Password and gesture entry remain outside the initial view and open from **⚙️ Try another sign-in method**.

## Password and feedback

- The password container has an accessible eye button with live show/hide state.
- Empty identifiers, empty passwords, password mismatch, incomplete patterns, pattern mismatch and inactive accounts receive specific inline messages.
- Caps Lock is reported beside the password while typing.
- Kiosk unlock also receives a visibility button and immediate empty-field feedback.

## Accessible gesture entry

- Large numbered hit targets support drawing, tapping and keyboard entry.
- Arrow keys move between targets; Home and End jump to the first and last; Enter or Space selects.
- Every target exposes `aria-pressed`, the group exposes an accessible label, and a polite live region announces progress.
- A visible **🧹 Clear Grid** button replaces the old double-tap behavior. Admin pattern editors receive the same generated control.

## Layout and polish

- Legal and creator metadata is separated into a low-contrast absolute bottom strip.
- Inputs, selectors, checkbox rows and confirmation cards provide hover, focus and pressed feedback.
- Reduced-motion mode suppresses skeleton and fallback transitions.

No database migration is required.
