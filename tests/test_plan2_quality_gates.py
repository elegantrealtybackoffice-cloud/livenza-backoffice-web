from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/'web'

def test_playwright_discovery_and_keyboard_journeys_are_defined():
    config=WEB/'playwright.config.ts'; spec=WEB/'e2e/discovery.spec.ts'
    assert config.exists() and spec.exists()
    text=spec.read_text()
    for token in ['390','844','LIVE MORE.','Jaipur','keyboard','Tab','desktop']:
        assert token.lower() in text.lower()
    assert 'PLAYWRIGHT_BASE_URL' in config.read_text()


def test_bundle_budget_script_and_ci_commands_are_defined():
    script=WEB/'scripts/check-bundle-budget.mjs'
    assert script.exists()
    t=script.read_text()
    assert 'build-manifest.json' in t
    assert '250 * 1024' in t
    assert '180 * 1024' in t
    package=json.loads((WEB/'package.json').read_text())
    assert package['scripts']['check:bundle'] == 'node scripts/check-bundle-budget.mjs'
    assert package['scripts']['test:e2e'] == 'playwright test'


def test_plan2_has_no_obvious_internal_dead_href_targets():
    # The route set intentionally includes the Plan 3 booking handoff.
    expected=['/','/stays','/store','/fit','/groom','/skin','/media','/life','/about','/contact','/account','/stays/book']
    for route in expected[1:]:
        page=WEB/f"src/app/{route.strip('/')}/page.tsx"
        assert page.exists(), route

def test_consumer_environment_contract_is_documented():
    env=(ROOT/'.env.example').read_text()
    assert 'LIVENZA_API_ORIGIN=' in env
    assert 'LIVENZA_SITE_URL=' in env
    readme=(ROOT/'README.md').read_text()
    assert 'Livenza.life consumer web' in readme
    assert 'web/' in readme

def test_global_css_imports_precede_all_style_rules():
    css=(WEB/'src/app/globals.css').read_text().splitlines()
    seen_rule=False
    for line in css:
        stripped=line.strip()
        if not stripped or stripped.startswith('/*'):
            continue
        if stripped.startswith('@import'):
            assert not seen_rule, '@import must precede all other CSS rules'
        else:
            seen_rule=True
