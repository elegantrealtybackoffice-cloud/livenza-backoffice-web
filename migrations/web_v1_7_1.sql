-- Tesla OS 27 historical compatibility: separate encrypted Landlord/Tenant Masters and immutable master documents.
CREATE TABLE IF NOT EXISTS landlord_master (
    id SERIAL PRIMARY KEY,
    master_code VARCHAR(32) NOT NULL UNIQUE,
    profile_name VARCHAR(180) NOT NULL,
    party_type VARCHAR(40) DEFAULT 'individual',
    legal_name VARCHAR(220) DEFAULT '',
    primary_mobile VARCHAR(40) DEFAULT '',
    email VARCHAR(220) DEFAULT '',
    city VARCHAR(120) DEFAULT '',
    state VARCHAR(120) DEFAULT '',
    country VARCHAR(120) DEFAULT 'India',
    verification_status VARCHAR(40) DEFAULT 'unverified',
    tags VARCHAR(500) DEFAULT '',
    search_text TEXT DEFAULT '',
    identifier_lookup_json TEXT DEFAULT '[]',
    active BOOLEAN DEFAULT TRUE,
    encrypted_payload TEXT NOT NULL DEFAULT '',
    encrypted_nonce TEXT NOT NULL DEFAULT '',
    legacy_profile_id INTEGER UNIQUE,
    created_by_user_id INTEGER REFERENCES "user"(id),
    updated_by_user_id INTEGER REFERENCES "user"(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_landlord_master_profile_name ON landlord_master(profile_name);
CREATE INDEX IF NOT EXISTS ix_landlord_master_legal_name ON landlord_master(legal_name);
CREATE INDEX IF NOT EXISTS ix_landlord_master_mobile ON landlord_master(primary_mobile);
CREATE INDEX IF NOT EXISTS ix_landlord_master_email ON landlord_master(email);
CREATE INDEX IF NOT EXISTS ix_landlord_master_city ON landlord_master(city);
CREATE INDEX IF NOT EXISTS ix_landlord_master_state ON landlord_master(state);
CREATE INDEX IF NOT EXISTS ix_landlord_master_active ON landlord_master(active);
CREATE INDEX IF NOT EXISTS ix_landlord_master_verification ON landlord_master(verification_status);

CREATE TABLE IF NOT EXISTS tenant_master (
    id SERIAL PRIMARY KEY,
    master_code VARCHAR(32) NOT NULL UNIQUE,
    profile_name VARCHAR(180) NOT NULL,
    party_type VARCHAR(40) DEFAULT 'individual',
    legal_name VARCHAR(220) DEFAULT '',
    primary_mobile VARCHAR(40) DEFAULT '',
    email VARCHAR(220) DEFAULT '',
    city VARCHAR(120) DEFAULT '',
    state VARCHAR(120) DEFAULT '',
    country VARCHAR(120) DEFAULT 'India',
    verification_status VARCHAR(40) DEFAULT 'unverified',
    tags VARCHAR(500) DEFAULT '',
    search_text TEXT DEFAULT '',
    identifier_lookup_json TEXT DEFAULT '[]',
    active BOOLEAN DEFAULT TRUE,
    encrypted_payload TEXT NOT NULL DEFAULT '',
    encrypted_nonce TEXT NOT NULL DEFAULT '',
    legacy_profile_id INTEGER UNIQUE,
    created_by_user_id INTEGER REFERENCES "user"(id),
    updated_by_user_id INTEGER REFERENCES "user"(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_tenant_master_profile_name ON tenant_master(profile_name);
CREATE INDEX IF NOT EXISTS ix_tenant_master_legal_name ON tenant_master(legal_name);
CREATE INDEX IF NOT EXISTS ix_tenant_master_mobile ON tenant_master(primary_mobile);
CREATE INDEX IF NOT EXISTS ix_tenant_master_email ON tenant_master(email);
CREATE INDEX IF NOT EXISTS ix_tenant_master_city ON tenant_master(city);
CREATE INDEX IF NOT EXISTS ix_tenant_master_state ON tenant_master(state);
CREATE INDEX IF NOT EXISTS ix_tenant_master_active ON tenant_master(active);
CREATE INDEX IF NOT EXISTS ix_tenant_master_verification ON tenant_master(verification_status);

CREATE TABLE IF NOT EXISTS master_document (
    id SERIAL PRIMARY KEY,
    owner_type VARCHAR(20) NOT NULL,
    landlord_master_id INTEGER REFERENCES landlord_master(id),
    tenant_master_id INTEGER REFERENCES tenant_master(id),
    category VARCHAR(80) NOT NULL,
    display_label VARCHAR(180) NOT NULL,
    storage_id VARCHAR(64) NOT NULL UNIQUE,
    extension VARCHAR(16) NOT NULL,
    mime_type VARCHAR(120) NOT NULL,
    ciphertext TEXT NOT NULL,
    nonce TEXT NOT NULL,
    issue_date DATE,
    expiry_date DATE,
    verification_status VARCHAR(40) DEFAULT 'unverified',
    replaced_document_id INTEGER,
    active BOOLEAN DEFAULT TRUE,
    uploaded_by_user_id INTEGER REFERENCES "user"(id),
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_master_document_owner CHECK (
      (landlord_master_id IS NOT NULL AND tenant_master_id IS NULL AND owner_type='landlord') OR
      (tenant_master_id IS NOT NULL AND landlord_master_id IS NULL AND owner_type='tenant')
    )
);
CREATE INDEX IF NOT EXISTS ix_master_document_storage_id ON master_document(storage_id);
CREATE INDEX IF NOT EXISTS ix_master_document_landlord ON master_document(landlord_master_id);
CREATE INDEX IF NOT EXISTS ix_master_document_tenant ON master_document(tenant_master_id);
CREATE INDEX IF NOT EXISTS ix_master_document_category ON master_document(category);
CREATE INDEX IF NOT EXISTS ix_master_document_expiry ON master_document(expiry_date);
CREATE INDEX IF NOT EXISTS ix_master_document_active ON master_document(active);

-- agreement_party_profile is intentionally retained for rollback/read compatibility.
