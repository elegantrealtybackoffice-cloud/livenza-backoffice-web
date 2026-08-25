# Livenza Life Operations Cloud — Web 1.9.0

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

The migration is additive and must not drop or rewrite Agreement, Landlord Master, Tenant Master, Electricity, Integrations Center or v1.8.0 3D-host data.

## Verification target

After deployment, `/version` should report:

**Web 1.9.0**

The response should include Letterhead Studio feature flags such as `letterhead-studio`, `mandatory-final-review`, `immutable-letterhead-pdf`, and `letterhead-document-vault`.
