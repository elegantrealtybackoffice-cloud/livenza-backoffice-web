from pathlib import Path

BASE = Path("templates/base.html").read_text(encoding="utf-8")
GROUPS = Path("templates/_application_groups.html").read_text(encoding="utf-8")
CSS = Path("static/home_light.css").read_text(encoding="utf-8")


def test_dashboard_launcher_uses_dynamic_registry():
    assert 'class="light-suite-grid"' not in BASE
    assert "appgroups.render_application_groups('launcher')" in BASE


def test_dynamic_launcher_uses_light_card_markup():
    launcher = GROUPS.split(
        "{% if surface == 'launcher' %}", 1
    )[1].split(
        "{% elif surface == 'drawer' %}", 1
    )[0]

    assert 'class="light-suite-card lg-app-tile"' in launcher
    assert "<small>{{desc}}</small>" in launcher
    assert "icons.symbol(symbol_name)" in launcher


def test_launcher_exposes_all_registry_categories():
    assert "surface != 'launcher'" in GROUPS
    assert ".suites-launcher .app-category-stage" in CSS
    assert ".suites-launcher .app-category-panel" in CSS
    assert ".suites-launcher .suite-launch-grid" in CSS