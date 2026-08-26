-- Tesla OS 27 historical compatibility additive migration. No v1.7.1 table is dropped or renamed.
CREATE TABLE IF NOT EXISTS integration_provider (
  id SERIAL PRIMARY KEY,
  provider_key VARCHAR(80) NOT NULL UNIQUE,
  display_name VARCHAR(180) NOT NULL,
  category VARCHAR(60) NOT NULL,
  workflow_module VARCHAR(60) NOT NULL DEFAULT 'integrations',
  portal_url TEXT DEFAULT '', developer_url TEXT DEFAULT '', embed_mode VARCHAR(24) DEFAULT 'external',
  capabilities_json TEXT DEFAULT '[]', active BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_integration_provider_category ON integration_provider(category);
CREATE INDEX IF NOT EXISTS ix_integration_provider_active ON integration_provider(active);

CREATE TABLE IF NOT EXISTS integration_connection (
  id SERIAL PRIMARY KEY,
  provider_id INTEGER NOT NULL REFERENCES integration_provider(id),
  display_name VARCHAR(180) NOT NULL, property_scope VARCHAR(180) DEFAULT '',
  source_mode VARCHAR(24) DEFAULT 'native', status VARCHAR(32) DEFAULT 'unconfigured',
  nonsecret_config_json TEXT DEFAULT '{}', last_test_status VARCHAR(32) DEFAULT '', last_test_message TEXT DEFAULT '',
  last_tested_at TIMESTAMP, last_success_status VARCHAR(32) DEFAULT '', last_success_message TEXT DEFAULT '', last_success_at TIMESTAMP,
  active BOOLEAN DEFAULT TRUE, created_by_user_id INTEGER REFERENCES "user"(id), updated_by_user_id INTEGER REFERENCES "user"(id),
  created_at TIMESTAMP, updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_integration_connection_provider_id ON integration_connection(provider_id);
CREATE INDEX IF NOT EXISTS ix_integration_connection_status ON integration_connection(status);
CREATE INDEX IF NOT EXISTS ix_integration_connection_property_scope ON integration_connection(property_scope);

CREATE TABLE IF NOT EXISTS integration_secret_ref (
  id SERIAL PRIMARY KEY,
  connection_id INTEGER NOT NULL REFERENCES integration_connection(id),
  secret_name VARCHAR(80) NOT NULL,
  vault_secret_id INTEGER NOT NULL REFERENCES vault_secret(id),
  created_at TIMESTAMP, updated_at TIMESTAMP,
  CONSTRAINT uq_integration_connection_secret UNIQUE(connection_id, secret_name)
);
CREATE INDEX IF NOT EXISTS ix_integration_secret_ref_connection_id ON integration_secret_ref(connection_id);

CREATE TABLE IF NOT EXISTS mascot_preference (
  id SERIAL PRIMARY KEY,
  user_id INTEGER NOT NULL UNIQUE REFERENCES "user"(id),
  enabled BOOLEAN DEFAULT TRUE, intensity VARCHAR(24) DEFAULT 'full', size VARCHAR(16) DEFAULT 'medium',
  position VARCHAR(24) DEFAULT 'bottom-right', operational_updates BOOLEAN DEFAULT TRUE,
  motivational_messages BOOLEAN DEFAULT TRUE, weather_reactions BOOLEAN DEFAULT TRUE,
  weather_city VARCHAR(120) DEFAULT 'Gurugram', updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_mascot_preference_user_id ON mascot_preference(user_id);
