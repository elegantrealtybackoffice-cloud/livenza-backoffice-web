from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
MIGRATION = ROOT / 'migrations' / 'livenza_v1_admin_migration.sql'


def test_new_admin_module_keys_are_explicit():
    for key in ['customers', 'stays_admin', 'store_admin', 'content']:
        assert f"'{key}':" in APP


def test_admin_models_are_present_with_required_unique_constraints():
    for model in ['ContentEntry', 'PropertyMedia', 'LegacyEntityMap', 'NotificationDelivery']:
        assert f'class {model}(db.Model):' in APP
    assert "name='uq_content_entry_key_locale'" in APP
    assert "name='uq_legacy_entity_source_key'" in APP


def test_admin_migration_defines_all_plan5_tables():
    assert MIGRATION.exists()
    sql = MIGRATION.read_text(encoding='utf-8').lower()
    for table in ['content_entry', 'property_media', 'legacy_entity_map', 'notification_delivery']:
        assert f'create table if not exists {table}' in sql
    assert 'uq_legacy_entity_source_key' in sql
