-- Livenza Web 1.9.0 additive migration. Existing Agreement/Master/Vault/Integration tables are preserved.
ALTER TABLE "user" ADD COLUMN IF NOT EXISTS capabilities_json TEXT DEFAULT '[]';

CREATE TABLE IF NOT EXISTS letterhead_template (
  id SERIAL PRIMARY KEY, name VARCHAR(160) NOT NULL, slug VARCHAR(180) NOT NULL UNIQUE,
  entity_scope VARCHAR(160) DEFAULT '', property_scope VARCHAR(160) DEFAULT '', document_family_scope VARCHAR(160) DEFAULT '',
  status VARCHAR(24) NOT NULL DEFAULT 'draft', current_published_version_id INTEGER,
  created_by_user_id INTEGER NOT NULL REFERENCES "user"(id), created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_letterhead_template_slug ON letterhead_template(slug);
CREATE INDEX IF NOT EXISTS ix_letterhead_template_status ON letterhead_template(status);

CREATE TABLE IF NOT EXISTS letterhead_template_version (
  id SERIAL PRIMARY KEY, template_id INTEGER NOT NULL REFERENCES letterhead_template(id), version_no INTEGER NOT NULL,
  lifecycle_state VARCHAR(24) NOT NULL DEFAULT 'draft', layout_json TEXT NOT NULL DEFAULT '{}', scope_json TEXT NOT NULL DEFAULT '{}',
  content_hash VARCHAR(64) NOT NULL DEFAULT '', submitted_by_user_id INTEGER REFERENCES "user"(id), submitted_at TIMESTAMP,
  published_by_user_id INTEGER REFERENCES "user"(id), published_at TIMESTAMP, rejection_comment TEXT NOT NULL DEFAULT '', created_at TIMESTAMP,
  CONSTRAINT uq_letterhead_template_version UNIQUE(template_id, version_no)
);
CREATE INDEX IF NOT EXISTS ix_letterhead_template_version_template_id ON letterhead_template_version(template_id);
CREATE INDEX IF NOT EXISTS ix_letterhead_template_version_state ON letterhead_template_version(lifecycle_state);

CREATE TABLE IF NOT EXISTS letterhead_asset (
  id SERIAL PRIMARY KEY, asset_kind VARCHAR(40) NOT NULL, owner_user_id INTEGER NOT NULL REFERENCES "user"(id),
  mime_type VARCHAR(80) NOT NULL, encrypted_asset BYTEA NOT NULL, sha256 VARCHAR(64) NOT NULL, display_name VARCHAR(240) NOT NULL DEFAULT '',
  is_active BOOLEAN NOT NULL DEFAULT TRUE, created_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_letterhead_asset_kind ON letterhead_asset(asset_kind);
CREATE INDEX IF NOT EXISTS ix_letterhead_asset_owner ON letterhead_asset(owner_user_id);
CREATE INDEX IF NOT EXISTS ix_letterhead_asset_sha256 ON letterhead_asset(sha256);

CREATE TABLE IF NOT EXISTS signature_asset (
  id SERIAL PRIMARY KEY, asset_kind VARCHAR(24) NOT NULL DEFAULT 'signature', signatory_name VARCHAR(160) NOT NULL,
  designation VARCHAR(160) NOT NULL DEFAULT '', scope_json TEXT NOT NULL DEFAULT '{}', encrypted_asset BYTEA NOT NULL,
  mime_type VARCHAR(80) NOT NULL, effective_date DATE, expires_at DATE, revoked_at TIMESTAMP, is_active BOOLEAN NOT NULL DEFAULT TRUE,
  created_by_user_id INTEGER REFERENCES "user"(id), created_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_signature_asset_active ON signature_asset(is_active);

CREATE TABLE IF NOT EXISTS letterhead_document (
  id SERIAL PRIMARY KEY, title VARCHAR(240) NOT NULL, document_family VARCHAR(80) NOT NULL DEFAULT 'custom',
  lifecycle_state VARCHAR(24) NOT NULL DEFAULT 'draft', creator_user_id INTEGER NOT NULL REFERENCES "user"(id),
  property_ref VARCHAR(160) NOT NULL DEFAULT '', entity_ref VARCHAR(160) NOT NULL DEFAULT '', source_refs_json TEXT NOT NULL DEFAULT '[]',
  current_revision_id INTEGER, finalized_revision_id INTEGER, created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_letterhead_document_creator ON letterhead_document(creator_user_id);
CREATE INDEX IF NOT EXISTS ix_letterhead_document_state ON letterhead_document(lifecycle_state);
CREATE INDEX IF NOT EXISTS ix_letterhead_document_family ON letterhead_document(document_family);

CREATE TABLE IF NOT EXISTS letterhead_document_revision (
  id SERIAL PRIMARY KEY, document_id INTEGER NOT NULL REFERENCES letterhead_document(id), revision_no INTEGER NOT NULL,
  structured_content_json TEXT NOT NULL DEFAULT '{}', template_version_id INTEGER REFERENCES letterhead_template_version(id),
  signature_asset_id INTEGER REFERENCES signature_asset(id), reference_number VARCHAR(160) NOT NULL DEFAULT '', status VARCHAR(24) NOT NULL DEFAULT 'draft',
  encrypted_pdf BYTEA, pdf_sha256 VARCHAR(64) NOT NULL DEFAULT '', approved_by_user_id INTEGER REFERENCES "user"(id), approved_at TIMESTAMP,
  finalized_at TIMESTAMP, created_at TIMESTAMP, CONSTRAINT uq_letterhead_document_revision UNIQUE(document_id, revision_no)
);
CREATE INDEX IF NOT EXISTS ix_letterhead_revision_document ON letterhead_document_revision(document_id);
CREATE INDEX IF NOT EXISTS ix_letterhead_revision_reference ON letterhead_document_revision(reference_number);
CREATE INDEX IF NOT EXISTS ix_letterhead_revision_status ON letterhead_document_revision(status);

CREATE TABLE IF NOT EXISTS document_attachment_link (
  id SERIAL PRIMARY KEY, revision_id INTEGER NOT NULL REFERENCES letterhead_document_revision(id), source_kind VARCHAR(80) NOT NULL,
  source_id VARCHAR(120) NOT NULL, suggested_by_ai BOOLEAN NOT NULL DEFAULT FALSE, approved_by_user BOOLEAN NOT NULL DEFAULT FALSE,
  approved_by_user_id INTEGER REFERENCES "user"(id), approved_at TIMESTAMP, created_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_document_attachment_revision ON document_attachment_link(revision_id);

CREATE TABLE IF NOT EXISTS document_delivery (
  id SERIAL PRIMARY KEY, revision_id INTEGER NOT NULL REFERENCES letterhead_document_revision(id), channel VARCHAR(24) NOT NULL,
  recipient VARCHAR(320) NOT NULL, state VARCHAR(24) NOT NULL DEFAULT 'pending', provider_name VARCHAR(80) NOT NULL DEFAULT '',
  provider_reference VARCHAR(240) NOT NULL DEFAULT '', attempt_no INTEGER NOT NULL DEFAULT 1, error_code VARCHAR(120) NOT NULL DEFAULT '',
  created_at TIMESTAMP, completed_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_document_delivery_revision ON document_delivery(revision_id);
CREATE INDEX IF NOT EXISTS ix_document_delivery_state ON document_delivery(state);
CREATE INDEX IF NOT EXISTS ix_document_delivery_channel ON document_delivery(channel);

CREATE TABLE IF NOT EXISTS document_sequence (
  id SERIAL PRIMARY KEY, sequence_key VARCHAR(220) NOT NULL UNIQUE, next_value INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX IF NOT EXISTS ix_document_sequence_key ON document_sequence(sequence_key);
