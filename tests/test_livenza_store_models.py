from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP_SOURCE = (ROOT / 'app.py').read_text(encoding='utf-8')
MIGRATION = ROOT / 'migrations' / 'livenza_v1_store_loyalty.sql'


def test_store_models_are_declared_in_app_source():
    for name in ['Product','ProductVariant','StoreOrder','StoreOrderItem','LoyaltyAccount','LoyaltyLedgerEntry']:
        assert f'class {name}(db.Model):' in APP_SOURCE


def test_store_model_contracts_include_unique_sku_and_loyalty_effect():
    assert "__tablename__ = 'product_variant'" in APP_SOURCE
    assert "sku = db.Column(db.String(100), unique=True" in APP_SOURCE
    assert "name='uq_loyalty_source_effect'" in APP_SOURCE


def test_store_migration_contains_all_tables_and_constraints():
    text = MIGRATION.read_text(encoding='utf-8')
    for table in ['product','product_variant','store_order','store_order_item','loyalty_account','loyalty_ledger_entry']:
        assert f'CREATE TABLE IF NOT EXISTS {table}' in text
    assert 'uq_loyalty_source_effect' in text
    assert 'stock_on_hand' in text and 'stock_reserved' in text


def test_runtime_store_models_exist_when_flask_is_available(app_module):
    for name in ['Product','ProductVariant','StoreOrder','StoreOrderItem','LoyaltyAccount','LoyaltyLedgerEntry']:
        assert hasattr(app_module, name)
