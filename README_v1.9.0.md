# Livenza Life Operations Cloud — Web 1.9.0




## Web 1.9.0 Maintenance — Liquid Glass UI, iMac/5K & Live Mascot

- Introduces one site-wide **Livenza Liquid Glass** material system with deep navy/blue/violet wallpaper, translucent layered surfaces, white compact system typography and consistent active/inactive icon states.
- Adds an original Livenza abstract wallpaper asset (`static/livenza_liquid_wallpaper.webp`) with a lighter low-capability rendering path; no Apple artwork, marks or proprietary icon assets are included.
- Completes a 52-template text-fit audit: important labels, headings, cards, forms and vault values wrap and grow naturally instead of relying on ellipsis or hidden overflow.
- Verifies responsive geometry from **390×844 through 5120×2880**, including 2560×1440, 2880×1800 and 3200×1800 iMac/large-monitor layouts. Large screens use a bounded 2160px content canvas and additional application-grid columns instead of oversized cards or excessively long text lines.
- Keeps the original blue robot **persistently available across authenticated pages** when enabled. Lightweight idle motion remains active in mobile/low-capability/TV performance modes unless the operating system explicitly requests reduced motion.
- Live mascot operations refresh every two minutes, pause while the page is hidden, resume on return, recover immediately after browser online/back-forward page restoration, retain the last safe state during network failures and visually react when safe operational summary values change.
- Restores the blue robot to the login welcome experience and removes visible “3D host” labeling from current mascot settings. Compatibility setting keys remain internal so existing deployments do not require a migration.
- Replaces primary grouped-navigation glyphs with custom `currentColor` SVG geometry and synchronizes selected/pressed/on/off state styling for Liquid Glass controls.
- No database migration is required for this visual/interaction maintenance layer.

## Web 1.9.0 Maintenance — Motion, Marquee & Text Reliability

- Decouples ordinary UI capability from WebGL availability so missing WebGL no longer disables the lightweight blue-robot mascot or general interface motion.
- Restores the blue robot, live operations marquee and lightweight card/reveal transitions in normal motion mode, including mobile/low-capability performance profiles.
- Rebuilds the live marquee as a measured two-group seamless loop that restarts after live-data refresh and resizes without duplicated static rows.
- Makes shared text-bearing cards, page heads, forms and status surfaces content-driven so wrapped copy grows vertically instead of being clipped or hidden.
- Removes unsafe `content-visibility`/paint-containment optimizations from text-heavy UI while retaining clipping only for explicit media, masks and local scrolling surfaces.
- Keeps `prefers-reduced-motion` authoritative: users who explicitly request reduced motion receive static mascot/marquee behavior with readable local marquee scrolling.
- No database migration is required for this maintenance update.

## Web 1.9.0 Maintenance — Blue Robot & Grouped UI

- Restores the original blue Livenza robot as the default live mascot and removes the WebGL 3D host runtime from the default page shell.
- Rebuilds Mascot Settings with responsive native controls while preserving existing preference compatibility and Admin policy keys.
- Replaces the long hamburger application list with categorized tabs and a responsive application grid.
- Uses the same shared application catalog on Home and in the three-line menu, including **Livenza Letterhead Studio** from Web 1.9.0.
- Adds site-wide text wrapping, touch-target, translucent mascot-chat, reduced-motion and low-capability performance hardening.
- No database migration is required for this maintenance update.

## Livenza Letterhead Studio

Web 1.9.0 adds the **Livenza Letterhead Studio** on top of the verified **v1.8.0** platform. v1.8.0 must already be deployed or merged because Letterhead Studio consumes the centralized **Integrations Center**, role-aware permissions, TV/layout primitives, and Vault-backed secret handling introduced there.

### What is included

- **Ask Livenza AI** for natural-language document requests such as residence certificates, no-dues certificates, authorization letters, employee letters and custom official correspondence.
- Permission-aware connected-data lookup from approved Livenza records, with protected source access audited and sensitive data minimized before AI use.
- Manual/hybrid document drafting with structured content, controlled autosave and explicit attachment decisions.
- Multiple user-authored letterhead template drafts with **Admin-only publication** of official versions.
- Protected signature/seal assets with scope, effective dates, expiry and revocation controls.
- Mandatory **Final Review** before any document can be finalized, downloaded, emailed or sent on WhatsApp.
- Immutable A4 PDF issuance with automatic reference numbering, revisions and approved annexures.
- Automatic searchable **Document Vault** containing the finalized PDF, template version, source summary, revision chain, delivery history and approved attachments.
- Email and WhatsApp delivery through providers configured only in the centralized **Integrations Center**. Letterhead Studio does not collect provider secrets.
- Retryable delivery records with provider references and success/failure states.

## Deployment prerequisites

1. Deploy or merge **v1.8.0** first.
2. Keep `LIVENZA_VAULT_MASTER_KEY` configured and stable in Render/production. It protects finalized PDFs, signatures/seals and other protected Letterhead assets at rest.
3. Apply `migrations/web_v1_9_0.sql` when the managed PostgreSQL/Supabase role cannot create the new tables automatically.
4. Configure AI, Email and WhatsApp providers only through **Admin → Integrations Center**. Do not add provider secrets to Letterhead templates, source code or GitHub.

### Provider configuration

- **AI / OpenAI:** configured in Integrations Center. The existing `OPENAI_API_KEY` environment fallback remains supported where already deployed, but the centralized integration is preferred.
- **Email:** uses the connected Google/Gmail integration.
- **WhatsApp:** uses the configured WhatsApp Cloud API integration.

A provider being unconfigured never blocks manual drafting or access to already finalized documents. It only disables the relevant AI/delivery action until the integration is connected.

## Security and issuance rules

- Finalized PDFs and protected signature/seal assets are encrypted at rest with the existing Livenza Vault cryptographic layer.
- Protected Aadhaar/PAN/passport/bank/supporting documents are not automatically attached. AI may suggest an attachment, but the user must explicitly approve it.
- AI cannot expand the current user's permissions.
- Raw sensitive identity/bank values and provider secrets must not be written to audit metadata.
- PDF downloads use `Cache-Control: no-store, private` and are audited using document/revision/reference identifiers only.
- Finalized documents and published template versions are immutable. Any later change creates a new revision/version.

## Historical documents

Existing PDFs from earlier releases are left untouched. Web 1.9.0 does **not** automatically reconstruct historical PDFs into the new Document Vault because reliable template/source metadata may not exist for those files. They may be imported separately in a future controlled workflow.

## Database migration

Use:

`migrations/web_v1_9_0.sql`

The migration is additive and must not drop or rewrite Agreement, Landlord Master, Tenant Master, Electricity, Integrations Center or legacy v1.8.0 mascot-preference data.

## Verification target

After deployment, `/version` should report:

**Web 1.9.0**

The response should include Letterhead Studio feature flags such as `letterhead-studio`, `mandatory-final-review`, `immutable-letterhead-pdf`, and `letterhead-document-vault`.

## Light Aqua Liquid Glass Refinement

The Web 1.9.0 maintenance UI now uses a light aqua, high-transparency Liquid Glass presentation across the authenticated workspace. The original Livenza wallpaper is washed into a high-key sky/aqua composition so the background remains visible through translucent cards, tabs, drawers, forms and controls while white interface text retains contrast through local glass tint and subtle text shadow.

Typography is intentionally more compact: page titles are capped at 40px, section/card/body/meta sizes use bounded responsive scales, and text-bearing containers grow with content instead of clipping. The repository-wide text audit covers all 52 Jinja templates plus the Integrations and Letterhead feature stylesheets. Dense tables and tab rails use local scrolling rather than page overflow.

Legacy module-specific opaque styling for Food Hub tabs, portal tabs, query-sheet cells, agreement accordions, mascot settings, popover menus and integration cards is superseded by the same final Light Aqua Liquid Glass contract. Printable agreement/document paper remains dark text on white.

The persistent blue mascot, live operational/weather updates, Ask Livenza panel and marquee motion remain part of the shared authenticated shell. Performance profiles reduce blur cost without reverting the site to dark opaque surfaces or freezing the mascot/marquee.

## Medium Aqua Adaptive Liquid Glass Refinement

The Web 1.9.0 interface now uses a medium aqua/blue wallpaper environment with adaptive glass hierarchy inspired by the interaction principles in Apple's official Liquid Glass guidance while remaining an original Livenza design. Functional elements such as navigation, segmented controls, toolbars, menus, drawers, popovers and mascot controls use the stronger refractive/tinted material; content cards, forms and tables use a calmer translucent material so information remains visually primary.

The final theme is isolated in `static/theme_v190.css` and is loaded after feature stylesheets, preventing Letterhead Studio or Integrations Center from silently overriding the site-wide material contract. Selected segmented controls use a high-contrast milky glass state, inactive controls remain transparent, and status/icon color is restrained to meaningful active/on states.

The background is intentionally darker than the previous Light Aqua maintenance build to improve white-text readability while keeping the original Livenza wallpaper visible. Text remains content-driven: meaningful labels and copy wrap, cards grow with content, dense tables scroll locally, and printable/document paper remains white with dark text.

Browser acceptance remains mobile through 5K/iMac class widths, and the persistent animated blue mascot continues live operational/weather polling and Ask Livenza behavior without using the retired WebGL host.

## Refractive Liquid Glass v2 Maintenance

The final Web 1.9.0 presentation layer now loads `static/theme_v190_refractive.css` after the Medium Aqua baseline and every feature stylesheet. Navigation, segmented controls, toolbars and compact actions use a stronger floating functional material with subtle specular edge light and reduced visible borders; selected segments use a bright milky lens with dark text; content cards stay calmer; drawers, menus and the persistent mascot assistant use thicker popover glass for readability.

The polish pass keeps the existing compact typography/text-fit contract, persistent animated blue mascot, live operational/weather refresh, Ask Livenza, marquee motion, reduced-motion accessibility and mobile-to-5K layout constraints. Text-bearing buttons and tabs grow with wrapped copy instead of clipping their content. Lower-capability profiles retain the material hierarchy while disabling the more expensive blur/specular optics.

## Golden Glass UI Maintenance

The Web 1.9.0 shell now uses the original **Livenza Golden Glass** final material layer: a graphite/charcoal environment with champagne reflections, neutral smoked functional glass, milky selected lenses, calmer content material, thicker readable popovers, and restrained Livenza cool-blue accents. Active icons transition from silver to champagne/cool luminosity with a short settle animation; reduced-motion users receive the final state without animation. The blue mascot, live operational/weather updates, Ask Livenza, marquee, Letterhead Studio, Integrations and all business workflows are unchanged.

Text-bearing controls remain content-driven and must not use optical clipping. Browser regression coverage includes mobile, desktop, iMac-class and 5K viewports.
