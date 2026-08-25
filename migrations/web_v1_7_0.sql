CREATE TABLE IF NOT EXISTS electricity_provider (
 id SERIAL PRIMARY KEY, name VARCHAR(180) NOT NULL, state VARCHAR(120) NOT NULL DEFAULT '', city VARCHAR(120) NOT NULL DEFAULT '',
 official_website_url TEXT DEFAULT '', official_payment_url TEXT DEFAULT '', official_login_url TEXT DEFAULT '', identifier_types_json TEXT DEFAULT '[]',
 bbps_biller_id VARCHAR(120) DEFAULT '', supports_bbps_fetch BOOLEAN DEFAULT FALSE, supports_bbps_payment BOOLEAN DEFAULT FALSE,
 embedding_mode VARCHAR(24) DEFAULT 'external', workflow_mode VARCHAR(24) DEFAULT 'portal', active BOOLEAN DEFAULT TRUE, notes TEXT DEFAULT '',
 created_at TIMESTAMP, updated_at TIMESTAMP, CONSTRAINT uq_electricity_provider_scope UNIQUE(name,state,city)
);
CREATE TABLE IF NOT EXISTS vault_secret (
 id SERIAL PRIMARY KEY, secret_type VARCHAR(60) NOT NULL, label VARCHAR(180) NOT NULL, username_masked VARCHAR(180) DEFAULT '', ciphertext TEXT NOT NULL,
 nonce TEXT NOT NULL, key_version VARCHAR(24) DEFAULT 'v1', linked_provider_id INTEGER NULL REFERENCES electricity_provider(id), linked_connection_id INTEGER NULL,
 created_by_user_id INTEGER NULL REFERENCES "user"(id), updated_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS electricity_connection (
 id SERIAL PRIMARY KEY, city_id INTEGER NULL REFERENCES city(id), property_name VARCHAR(180) DEFAULT '', provider_id INTEGER NOT NULL REFERENCES electricity_provider(id),
 connection_name VARCHAR(180) DEFAULT '', consumer_name VARCHAR(180) DEFAULT '', identifier_primary VARCHAR(180) NOT NULL, identifier_primary_type VARCHAR(40) NOT NULL DEFAULT 'CONSUMER_NO',
 identifier_secondary VARCHAR(180) DEFAULT '', identifier_secondary_type VARCHAR(40) DEFAULT '', meter_number VARCHAR(120) DEFAULT '', billing_cycle VARCHAR(80) DEFAULT 'Monthly',
 reminder_days_before INTEGER DEFAULT 5, vault_credential_id INTEGER NULL REFERENCES vault_secret(id), status VARCHAR(32) DEFAULT 'active', last_fetch_status VARCHAR(48) DEFAULT '',
 last_fetch_at TIMESTAMP NULL, created_by_user_id INTEGER NULL REFERENCES "user"(id), created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS electricity_bill (
 id SERIAL PRIMARY KEY, connection_id INTEGER NOT NULL REFERENCES electricity_connection(id), provider_id INTEGER NOT NULL REFERENCES electricity_provider(id), dedupe_key VARCHAR(320) UNIQUE NOT NULL,
 bill_month VARCHAR(24) DEFAULT '', billing_period_start DATE NULL, billing_period_end DATE NULL, bill_number VARCHAR(140) DEFAULT '', bill_date DATE NULL, due_date DATE NULL,
 consumer_name VARCHAR(180) DEFAULT '', meter_number VARCHAR(120) DEFAULT '', units_consumed NUMERIC(14,3) NULL, previous_reading NUMERIC(14,3) NULL, current_reading NUMERIC(14,3) NULL,
 current_charges NUMERIC(14,2) DEFAULT 0, arrears_amount NUMERIC(14,2) DEFAULT 0, late_fee_amount NUMERIC(14,2) DEFAULT 0, net_amount NUMERIC(14,2) DEFAULT 0,
 total_due_amount NUMERIC(14,2) DEFAULT 0, status VARCHAR(48) DEFAULT 'unpaid', source_type VARCHAR(48) DEFAULT 'manual_entry', raw_source_meta_json TEXT DEFAULT '{}',
 receipt_file_path_or_token TEXT DEFAULT '', bill_file_path_or_token TEXT DEFAULT '', bill_file_name VARCHAR(255) DEFAULT '', bill_mime_type VARCHAR(120) DEFAULT '', encrypted_bill_blob BYTEA NULL, created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE TABLE IF NOT EXISTS electricity_payment (
 id SERIAL PRIMARY KEY, bill_id INTEGER NOT NULL REFERENCES electricity_bill(id), connection_id INTEGER NOT NULL REFERENCES electricity_connection(id), provider_id INTEGER NOT NULL REFERENCES electricity_provider(id),
 payment_provider VARCHAR(120) DEFAULT '', payment_reference VARCHAR(180) DEFAULT '', provider_txn_id VARCHAR(180) DEFAULT '', paid_amount NUMERIC(14,2) DEFAULT 0,
 initiated_at TIMESTAMP, confirmed_at TIMESTAMP NULL, status VARCHAR(48) DEFAULT 'initiated', receipt_path_or_token TEXT DEFAULT '', meta_json TEXT DEFAULT '{}'
);
CREATE TABLE IF NOT EXISTS reminder_item (
 id SERIAL PRIMARY KEY, module VARCHAR(60) NOT NULL DEFAULT 'electricity', entity_id INTEGER NOT NULL, title VARCHAR(240) NOT NULL, severity VARCHAR(24) DEFAULT 'info', due_at TIMESTAMP NULL,
 status VARCHAR(32) DEFAULT 'active', payload_json TEXT DEFAULT '{}', created_at TIMESTAMP, updated_at TIMESTAMP, CONSTRAINT uq_reminder_entity UNIQUE(module,entity_id)
);
CREATE TABLE IF NOT EXISTS audit_event (
 id SERIAL PRIMARY KEY, actor_user_id INTEGER NULL REFERENCES "user"(id), module VARCHAR(60) NOT NULL, action VARCHAR(120) NOT NULL, target_type VARCHAR(80) DEFAULT '', target_id INTEGER NULL,
 status VARCHAR(32) DEFAULT 'success', note TEXT DEFAULT '', meta_json TEXT DEFAULT '{}', created_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_electricity_provider_state_city ON electricity_provider(state, city);
CREATE INDEX IF NOT EXISTS ix_electricity_connection_provider ON electricity_connection(provider_id);
CREATE INDEX IF NOT EXISTS ix_electricity_bill_connection_due ON electricity_bill(connection_id, due_date);
CREATE INDEX IF NOT EXISTS ix_electricity_bill_status_due ON electricity_bill(status, due_date);
CREATE INDEX IF NOT EXISTS ix_electricity_payment_bill ON electricity_payment(bill_id);
CREATE INDEX IF NOT EXISTS ix_reminder_item_module_status ON reminder_item(module, status);
CREATE INDEX IF NOT EXISTS ix_audit_event_module_created ON audit_event(module, created_at);
