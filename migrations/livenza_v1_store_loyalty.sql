CREATE TABLE IF NOT EXISTS product (
  id INTEGER PRIMARY KEY,
  slug VARCHAR(180) NOT NULL UNIQUE,
  name VARCHAR(220) NOT NULL,
  brand VARCHAR(40) DEFAULT 'store',
  category VARCHAR(60) NOT NULL,
  collection VARCHAR(80) DEFAULT '',
  summary TEXT DEFAULT '',
  description TEXT DEFAULT '',
  active BOOLEAN DEFAULT TRUE,
  public BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_product_category ON product(category);
CREATE INDEX IF NOT EXISTS ix_product_collection ON product(collection);

CREATE TABLE IF NOT EXISTS product_variant (
  id INTEGER PRIMARY KEY,
  product_id INTEGER NOT NULL REFERENCES product(id),
  sku VARCHAR(100) NOT NULL UNIQUE,
  title VARCHAR(180) NOT NULL,
  price_minor INTEGER NOT NULL CHECK(price_minor >= 0),
  currency VARCHAR(3) DEFAULT 'INR',
  stock_on_hand INTEGER DEFAULT 0 CHECK(stock_on_hand >= 0),
  stock_reserved INTEGER DEFAULT 0 CHECK(stock_reserved >= 0),
  attributes_json TEXT DEFAULT '{}',
  active BOOLEAN DEFAULT TRUE
);
CREATE INDEX IF NOT EXISTS ix_product_variant_product ON product_variant(product_id);

CREATE TABLE IF NOT EXISTS store_order (
  id INTEGER PRIMARY KEY,
  public_id VARCHAR(36) NOT NULL UNIQUE,
  customer_id INTEGER NOT NULL REFERENCES customer(id),
  status VARCHAR(32) DEFAULT 'placed',
  fulfilment_mode VARCHAR(32) DEFAULT 'address',
  delivery_json TEXT DEFAULT '{}',
  subtotal_minor INTEGER DEFAULT 0,
  discount_minor INTEGER DEFAULT 0,
  delivery_minor INTEGER DEFAULT 0,
  total_minor INTEGER DEFAULT 0,
  created_at TIMESTAMP,
  updated_at TIMESTAMP
);
CREATE INDEX IF NOT EXISTS ix_store_order_customer ON store_order(customer_id);

CREATE TABLE IF NOT EXISTS store_order_item (
  id INTEGER PRIMARY KEY,
  order_id INTEGER NOT NULL REFERENCES store_order(id),
  variant_id INTEGER NOT NULL REFERENCES product_variant(id),
  sku VARCHAR(100) NOT NULL,
  product_name VARCHAR(220) NOT NULL,
  variant_title VARCHAR(180) NOT NULL,
  quantity INTEGER NOT NULL CHECK(quantity > 0),
  unit_price_minor INTEGER NOT NULL,
  line_total_minor INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_store_order_item_order ON store_order_item(order_id);

CREATE TABLE IF NOT EXISTS loyalty_account (
  id INTEGER PRIMARY KEY,
  customer_id INTEGER NOT NULL UNIQUE REFERENCES customer(id),
  status VARCHAR(24) DEFAULT 'active',
  created_at TIMESTAMP
);

CREATE TABLE IF NOT EXISTS loyalty_ledger_entry (
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL REFERENCES loyalty_account(id),
  direction VARCHAR(12) NOT NULL,
  points INTEGER NOT NULL CHECK(points >= 0),
  source_type VARCHAR(40) NOT NULL,
  source_id INTEGER NOT NULL,
  effect_key VARCHAR(120) NOT NULL,
  description VARCHAR(220) DEFAULT '',
  created_at TIMESTAMP,
  CONSTRAINT uq_loyalty_source_effect UNIQUE(source_type, source_id, effect_key)
);
CREATE INDEX IF NOT EXISTS ix_loyalty_ledger_account ON loyalty_ledger_entry(account_id);
