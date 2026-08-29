-- Livenza.life V1 foundation. Additive only: no legacy table drops/renames.
CREATE TABLE IF NOT EXISTS customer (
    id SERIAL PRIMARY KEY,
    public_id VARCHAR(36) NOT NULL UNIQUE,
    full_name VARCHAR(180) DEFAULT '',
    primary_mobile VARCHAR(40) DEFAULT '',
    primary_email VARCHAR(220) DEFAULT '',
    status VARCHAR(32) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_customer_public_id ON customer(public_id);
CREATE INDEX IF NOT EXISTS ix_customer_primary_mobile ON customer(primary_mobile);
CREATE INDEX IF NOT EXISTS ix_customer_primary_email ON customer(primary_email);
CREATE INDEX IF NOT EXISTS ix_customer_status ON customer(status);

CREATE TABLE IF NOT EXISTS customer_identity (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    provider VARCHAR(32) NOT NULL,
    identifier VARCHAR(220) NOT NULL,
    verified_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_customer_identity_provider_identifier UNIQUE(provider, identifier)
);
CREATE INDEX IF NOT EXISTS ix_customer_identity_customer_id ON customer_identity(customer_id);
CREATE INDEX IF NOT EXISTS ix_customer_identity_provider ON customer_identity(provider);
CREATE INDEX IF NOT EXISTS ix_customer_identity_identifier ON customer_identity(identifier);

CREATE TABLE IF NOT EXISTS customer_otp_challenge (
    id SERIAL PRIMARY KEY,
    identifier VARCHAR(220) NOT NULL,
    purpose VARCHAR(32) NOT NULL DEFAULT 'login',
    otp_hash VARCHAR(64) NOT NULL,
    salt VARCHAR(64) NOT NULL,
    attempts INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    consumed_at TIMESTAMP NULL,
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_customer_otp_identifier ON customer_otp_challenge(identifier);
CREATE INDEX IF NOT EXISTS ix_customer_otp_expires_at ON customer_otp_challenge(expires_at);
CREATE INDEX IF NOT EXISTS ix_customer_otp_requested_at ON customer_otp_challenge(requested_at);

CREATE TABLE IF NOT EXISTS customer_session (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    token_hash VARCHAR(64) NOT NULL UNIQUE,
    expires_at TIMESTAMP NOT NULL,
    revoked_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_customer_session_customer_id ON customer_session(customer_id);
CREATE INDEX IF NOT EXISTS ix_customer_session_token_hash ON customer_session(token_hash);
CREATE INDEX IF NOT EXISTS ix_customer_session_expires_at ON customer_session(expires_at);

CREATE TABLE IF NOT EXISTS customer_address (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customer(id),
    label VARCHAR(80) DEFAULT 'Home',
    recipient_name VARCHAR(180) DEFAULT '',
    mobile VARCHAR(40) DEFAULT '',
    line1 VARCHAR(240) DEFAULT '',
    line2 VARCHAR(240) DEFAULT '',
    city VARCHAR(120) DEFAULT '',
    state VARCHAR(120) DEFAULT '',
    postal_code VARCHAR(20) DEFAULT '',
    country VARCHAR(80) DEFAULT 'India',
    active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_customer_address_customer_id ON customer_address(customer_id);
CREATE INDEX IF NOT EXISTS ix_customer_address_active ON customer_address(active);

CREATE TABLE IF NOT EXISTS stay_property (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(160) NOT NULL UNIQUE,
    name VARCHAR(220) NOT NULL,
    city VARCHAR(120) NOT NULL,
    area VARCHAR(160) DEFAULT '',
    stay_types_json TEXT DEFAULT '["student"]',
    summary TEXT DEFAULT '',
    active BOOLEAN DEFAULT TRUE,
    public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_stay_property_slug ON stay_property(slug);
CREATE INDEX IF NOT EXISTS ix_stay_property_city ON stay_property(city);
CREATE INDEX IF NOT EXISTS ix_stay_property_area ON stay_property(area);
CREATE INDEX IF NOT EXISTS ix_stay_property_active ON stay_property(active);
CREATE INDEX IF NOT EXISTS ix_stay_property_public ON stay_property(public);

CREATE TABLE IF NOT EXISTS stay_room_category (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES stay_property(id),
    slug VARCHAR(120) NOT NULL,
    name VARCHAR(180) NOT NULL,
    occupancy INTEGER DEFAULT 1,
    summary TEXT DEFAULT '',
    active BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_room_category_property_slug UNIQUE(property_id, slug)
);
CREATE INDEX IF NOT EXISTS ix_stay_room_category_property_id ON stay_room_category(property_id);
CREATE INDEX IF NOT EXISTS ix_stay_room_category_active ON stay_room_category(active);

CREATE TABLE IF NOT EXISTS stay_inventory_unit (
    id SERIAL PRIMARY KEY,
    property_id INTEGER NOT NULL REFERENCES stay_property(id),
    parent_id INTEGER NULL REFERENCES stay_inventory_unit(id),
    room_category_id INTEGER NULL REFERENCES stay_room_category(id),
    unit_type VARCHAR(24) NOT NULL,
    code VARCHAR(80) NOT NULL,
    display_name VARCHAR(180) DEFAULT '',
    allocatable BOOLEAN DEFAULT FALSE,
    active BOOLEAN DEFAULT TRUE,
    CONSTRAINT uq_inventory_unit_path_code UNIQUE(property_id, parent_id, code)
);
CREATE INDEX IF NOT EXISTS ix_stay_inventory_property_id ON stay_inventory_unit(property_id);
CREATE INDEX IF NOT EXISTS ix_stay_inventory_parent_id ON stay_inventory_unit(parent_id);
CREATE INDEX IF NOT EXISTS ix_stay_inventory_room_category_id ON stay_inventory_unit(room_category_id);
CREATE INDEX IF NOT EXISTS ix_stay_inventory_unit_type ON stay_inventory_unit(unit_type);
CREATE INDEX IF NOT EXISTS ix_stay_inventory_allocatable ON stay_inventory_unit(allocatable);
CREATE INDEX IF NOT EXISTS ix_stay_inventory_active ON stay_inventory_unit(active);
