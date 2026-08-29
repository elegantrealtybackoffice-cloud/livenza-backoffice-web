-- Livenza.life V1 booking/payment schema. Additive only.
CREATE TABLE IF NOT EXISTS stay_rate_plan (
  id INTEGER PRIMARY KEY,
  property_id INTEGER NOT NULL REFERENCES stay_property(id),
  room_category_id INTEGER NOT NULL REFERENCES stay_room_category(id),
  code VARCHAR(80) NOT NULL,
  stay_type VARCHAR(32) NOT NULL,
  billing_period VARCHAR(32) NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  amount_minor INTEGER NOT NULL,
  security_deposit_minor INTEGER DEFAULT 0,
  reservation_amount_minor INTEGER DEFAULT 0,
  hold_minutes INTEGER DEFAULT 10,
  active BOOLEAN DEFAULT TRUE,
  CONSTRAINT uq_rate_plan_property_room_code UNIQUE(property_id, room_category_id, code)
);
CREATE INDEX IF NOT EXISTS ix_stay_rate_plan_property_id ON stay_rate_plan(property_id);
CREATE INDEX IF NOT EXISTS ix_stay_rate_plan_room_category_id ON stay_rate_plan(room_category_id);

CREATE TABLE IF NOT EXISTS stay_inventory_hold (
  id INTEGER PRIMARY KEY,
  public_id VARCHAR(36) NOT NULL UNIQUE,
  customer_id INTEGER NOT NULL REFERENCES customer(id),
  inventory_unit_id INTEGER NOT NULL REFERENCES stay_inventory_unit(id),
  rate_plan_id INTEGER NOT NULL REFERENCES stay_rate_plan(id),
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status VARCHAR(24) DEFAULT 'active',
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_stay_inventory_hold_window ON stay_inventory_hold(inventory_unit_id,start_date,end_date,status,expires_at);

CREATE TABLE IF NOT EXISTS stay_booking (
  id INTEGER PRIMARY KEY,
  public_id VARCHAR(36) NOT NULL UNIQUE,
  customer_id INTEGER NOT NULL REFERENCES customer(id),
  property_id INTEGER NOT NULL REFERENCES stay_property(id),
  rate_plan_id INTEGER NOT NULL REFERENCES stay_rate_plan(id),
  booking_mode VARCHAR(24) NOT NULL DEFAULT 'book_now',
  stay_type VARCHAR(32) NOT NULL,
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  status VARCHAR(32) DEFAULT 'held',
  subtotal_minor INTEGER DEFAULT 0,
  security_deposit_minor INTEGER DEFAULT 0,
  addon_total_minor INTEGER DEFAULT 0,
  total_minor INTEGER DEFAULT 0,
  amount_due_now_minor INTEGER DEFAULT 0,
  guardian_json TEXT DEFAULT '{}',
  details_json TEXT DEFAULT '{}',
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_stay_booking_customer_status ON stay_booking(customer_id,status);

CREATE TABLE IF NOT EXISTS stay_booking_item (
  id INTEGER PRIMARY KEY,
  booking_id INTEGER NOT NULL REFERENCES stay_booking(id),
  hold_id INTEGER NOT NULL UNIQUE REFERENCES stay_inventory_hold(id),
  inventory_unit_id INTEGER NOT NULL REFERENCES stay_inventory_unit(id)
);

CREATE TABLE IF NOT EXISTS booking_add_on (
  id INTEGER PRIMARY KEY,
  booking_id INTEGER NOT NULL REFERENCES stay_booking(id),
  code VARCHAR(80) NOT NULL,
  label VARCHAR(180) NOT NULL,
  amount_minor INTEGER DEFAULT 0,
  metadata_json TEXT DEFAULT '{}'
);

CREATE TABLE IF NOT EXISTS payment_record (
  id INTEGER PRIMARY KEY,
  public_id VARCHAR(36) NOT NULL UNIQUE,
  customer_id INTEGER NOT NULL REFERENCES customer(id),
  source_type VARCHAR(32) NOT NULL,
  source_id INTEGER NOT NULL,
  gateway VARCHAR(32) DEFAULT 'razorpay',
  gateway_order_id VARCHAR(120) UNIQUE,
  gateway_payment_id VARCHAR(120),
  amount_minor INTEGER NOT NULL,
  currency VARCHAR(3) DEFAULT 'INR',
  status VARCHAR(32) DEFAULT 'created',
  metadata_json TEXT DEFAULT '{}',
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS processed_webhook_event (
  id INTEGER PRIMARY KEY,
  gateway VARCHAR(32) NOT NULL,
  external_event_id VARCHAR(180) NOT NULL UNIQUE,
  event_type VARCHAR(120) NOT NULL,
  processed_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS customer_document (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL REFERENCES customer(id),
  booking_id INTEGER REFERENCES stay_booking(id),
  document_type VARCHAR(60) NOT NULL,
  display_name VARCHAR(180) NOT NULL,
  storage_key VARCHAR(320) NOT NULL UNIQUE,
  private BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS support_ticket (
  id INTEGER PRIMARY KEY,
  public_id VARCHAR(36) NOT NULL UNIQUE,
  customer_id INTEGER NOT NULL REFERENCES customer(id),
  category VARCHAR(40) NOT NULL,
  subject VARCHAR(180) NOT NULL,
  description TEXT NOT NULL,
  status VARCHAR(32) DEFAULT 'open',
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS booking_share_token (
  id INTEGER PRIMARY KEY,
  booking_id INTEGER NOT NULL REFERENCES stay_booking(id),
  token_hash VARCHAR(64) NOT NULL UNIQUE,
  expires_at TIMESTAMP NOT NULL,
  revoked_at TIMESTAMP,
  created_at TIMESTAMP
);
