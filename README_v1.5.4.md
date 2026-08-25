# Livenza Life Operations Cloud — Web 1.5.4

Web 1.5.4 applies a coherent translucent material system across the entire existing website while preserving its navigation, functionality, typography and animation language.

## Visual changes

- A fixed, softly graded hospitality photograph provides depth behind the light interface.
- Authenticated pages sit inside a large rounded translucent workspace shell inspired by the supplied reference.
- Cards, statistics, forms, tables, query sheets, integrations, menus, assistant surfaces and footer use coordinated glass opacity, blur, border and shadow levels.
- The header remains transparent at the top of a page and becomes stronger glass while scrolling.
- LIVE status, application, profile and display menus remain readable over page content without becoming visually heavy.
- Inputs and table cells retain enough opacity for dense operational work while still showing the surrounding depth.

## Preserved behavior

- Apple-style system typography and the existing white/navy palette.
- Stationary plain Livenza mark with AI light effects.
- Dashboard photo cards, contextual photo ribbons, hover tilt and page entrance motion.
- One-time dancing mascot after login.
- Fullscreen, rotation, Windows kiosk, WhatsApp, Gmail, Drive, food partner, marquee and admin workflows.
- Reduced-motion behavior, keyboard focus visibility, mobile layouts and print output.

## Deployment

Deploy this package in the same way as Web 1.5.3. No new database migration or environment variable is required for the visual update. The existing Web 1.5.0 integration migration and environment configuration remain required on installations that have not already applied them.

After deployment, confirm `/version` returns `Web 1.5.4` and includes `translucent-workspace-shell`, `sitewide-glass-material` and `photographic-depth-background`.
