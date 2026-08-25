# Livenza Back Office Web 1.5.3

## Login welcome sequence

After a successful password, pattern or fingerprint/passkey login, the Home dashboard consumes a one-time session trigger and displays the supplied Livenza mascot.

The sequence:

1. Enters from the side with a soft spotlight.
2. Greets the signed-in user by name.
3. Performs a short bouncing dance with sparkle effects.
4. Automatically exits and is removed from the page.

The welcome does not repeat on page refresh. Users can dismiss it with the close button or Escape. Reduced-motion preferences replace the dance with a simple fade.

## Deployment

No database migration or environment variable is required. Deploy normally and confirm `/version` reports `Web 1.5.3`.
