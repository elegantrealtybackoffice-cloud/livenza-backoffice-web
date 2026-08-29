from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'livenza_legacy_core.py'
SCRIPT=ROOT/'scripts/livenza_migrate_legacy.py'


def load_core():
    spec=importlib.util.spec_from_file_location('livenza_legacy_core',CORE)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def test_existing_mapping_always_wins():
    c=load_core()
    out=c.resolve_customer_action(mapped_customer_id=17,mobile_matches=[],email_matches=[])
    assert out=={'action':'link','customer_id':17,'reason':'existing_mapping'}


def test_verified_identity_conflict_is_not_silently_merged():
    c=load_core()
    out=c.resolve_customer_action(mapped_customer_id=None,mobile_matches=[4],email_matches=[9])
    assert out['action']=='conflict'


def test_display_name_is_never_a_link_signal():
    c=load_core()
    out=c.resolve_customer_action(mapped_customer_id=None,mobile_matches=[],email_matches=[],display_name_matches=[5])
    assert out['action']=='create'


def test_room_mapping_key_is_explicit_property_and_room():
    c=load_core()
    assert c.room_source_key(' Oasis Residency ',' 204 ')=='oasis residency|204'


def test_script_supports_dry_run_apply_source_and_strict_without_name_merge():
    assert SCRIPT.exists()
    text=SCRIPT.read_text(encoding='utf-8')
    for flag in ['--dry-run','--apply','--source','--strict']:
        assert flag in text
    assert 'display_name' not in text.lower() or 'never' in text.lower()
    assert 'LegacyEntityMap' in text
    assert 'dry_run' in text and 'db.session.commit()' in text
