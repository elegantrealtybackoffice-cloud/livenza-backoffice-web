CREATE TABLE IF NOT EXISTS content_entry (
  id INTEGER PRIMARY KEY,
  content_type VARCHAR(60) NOT NULL,
  key VARCHAR(180) NOT NULL,
  locale VARCHAR(12) DEFAULT 'en',
  status VARCHAR(24) DEFAULT 'draft',
  title VARCHAR(240) DEFAULT '',
  body_json TEXT DEFAULT '{}',
  seo_json TEXT DEFAULT '{}',
  updated_by_user_id INTEGER REFERENCES user(id),
  created_at TIMESTAMP,
  updated_at TIMESTAMP,
  CONSTRAINT uq_content_entry_key_locale UNIQUE(content_type, key, locale)
);
CREATE INDEX IF NOT EXISTS ix_content_entry_type_status ON content_entry(content_type, status);

CREATE TABLE IF NOT EXISTS property_media (
  id INTEGER PRIMARY KEY,
  property_id INTEGER NOT NULL REFERENCES stay_property(id),
  media_type VARCHAR(24) NOT NULL,
  storage_key VARCHAR(320) NOT NULL,
  alt_text VARCHAR(240) DEFAULT '',
  sort_order INTEGER DEFAULT 0,
  public BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_property_media_property ON property_media(property_id);

CREATE TABLE IF NOT EXISTS legacy_entity_map (
  id INTEGER PRIMARY KEY,
  source_system VARCHAR(80) NOT NULL,
  source_entity_type VARCHAR(80) NOT NULL,
  source_id VARCHAR(180) NOT NULL,
  livenza_entity_type VARCHAR(80) NOT NULL,
  livenza_entity_id INTEGER NOT NULL,
  metadata_json TEXT DEFAULT '{}',
  created_at TIMESTAMP,
  CONSTRAINT uq_legacy_entity_source_key UNIQUE(source_system, source_entity_type, source_id)
);
CREATE INDEX IF NOT EXISTS ix_legacy_entity_target ON legacy_entity_map(livenza_entity_type, livenza_entity_id);

CREATE TABLE IF NOT EXISTS notification_delivery (
  id INTEGER PRIMARY KEY,
  event_key VARCHAR(120) NOT NULL,
  customer_id INTEGER REFERENCES customer(id),
  channel VARCHAR(24) NOT NULL,
  destination_masked VARCHAR(180) DEFAULT '',
  status VARCHAR(24) DEFAULT 'pending',
  provider_message_id VARCHAR(180) DEFAULT '',
  error_code VARCHAR(80) DEFAULT '',
  attempts INTEGER DEFAULT 0,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_notification_delivery_event ON notification_delivery(event_key);
CREATE INDEX IF NOT EXISTS ix_notification_delivery_customer ON notification_delivery(customer_id);
