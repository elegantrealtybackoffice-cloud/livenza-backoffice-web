from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / 'app.py').read_text(encoding='utf-8')
GROUPS = (ROOT / 'templates' / '_application_groups.html').read_text(encoding='utf-8')
SYMBOLS = (ROOT / 'templates' / '_livenza_symbols.html').read_text(encoding='utf-8')
BASE = (ROOT / 'templates' / 'base.html').read_text(encoding='utf-8')


def test_module_and_registry_are_registered():
    assert "'staff_salary': 'Staff Salary Studio'" in APP
    assert "'title':'Staff Salary Studio'" in APP
    assert "'endpoint':'staff_salary_studio'" in APP
    assert "'permission':'staff_salary'" in APP
    assert "'icon':'staff_salary'" in APP


def test_finance_launcher_and_command_palette_include_staff_salary():
    assert "app_item(surface,'Staff Salary Studio'" in GROUPS
    assert "'staff_salary_studio','staff_salary','staff_salary'" in GROUPS
    assert "command_item('Staff Salary Studio'" in GROUPS


def test_staff_salary_symbol_exists():
    assert "name == 'staff_salary'" in SYMBOLS


def test_lightweight_shell_surfaces_are_permission_gated():
    assert "can_access('staff_salary')" in BASE
    assert "url_for('staff_salary_studio')" in BASE
    assert 'data-dock-app="staff_salary_studio"' in BASE
    assert 'data-command-label="Staff Salary Studio"' in BASE


def test_version_exposes_feature_flag():
    assert "'staff-salary-studio'" in APP
