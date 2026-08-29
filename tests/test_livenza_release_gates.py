from pathlib import Path
import importlib.util

ROOT=Path(__file__).resolve().parents[1]
CORE=ROOT/'livenza_admin_core.py'
APP=(ROOT/'app.py').read_text(encoding='utf-8')
API=(ROOT/'livenza_api_v1.py').read_text(encoding='utf-8')
SMOKE=(ROOT/'scripts/livenza_smoke.py')
E2E=(ROOT/'web/e2e/release.spec.ts')
NOT_FOUND=ROOT/'web/src/app/not-found.tsx'
RENDER=(ROOT/'render.yaml').read_text(encoding='utf-8')
ENV_EXAMPLE=(ROOT/'.env.example').read_text(encoding='utf-8')


def load_core():
    spec=importlib.util.spec_from_file_location('livenza_admin_core',CORE)
    mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod); return mod


def production_env(**updates):
    env={
        'LIVENZA_ENV':'production','CUSTOMER_AUTH_TEST_MODE':'0','SECRET_KEY':'x'*48,
        'DATABASE_URL':'postgresql://user:pass@db.example/livenza','FORCE_HTTPS':'1',
        'RAZORPAY_TEST_STUB':'0','RAZORPAY_KEY_ID':'rzp_live_123','RAZORPAY_KEY_SECRET':'live-secret','RAZORPAY_WEBHOOK_SECRET':'hook-secret',
        'SUPABASE_URL':'https://example.supabase.co','SUPABASE_SERVICE_ROLE_KEY':'service-role','LIVENZA_PRIVATE_BUCKET':'livenza-private',
    }
    env.update(updates); return env


def test_production_configuration_rejects_test_auth_defaults_and_missing_services():
    core=load_core()
    assert core.production_config_errors(production_env())==[]
    assert core.production_config_errors(production_env(CUSTOMER_AUTH_TEST_MODE='1'))
    assert core.production_config_errors(production_env(SECRET_KEY='change-this-secret-before-production'))
    assert core.production_config_errors(production_env(DATABASE_URL='sqlite:///x.db'))
    assert core.production_config_errors(production_env(RAZORPAY_WEBHOOK_SECRET=''))
    assert core.production_config_errors(production_env(SUPABASE_SERVICE_ROLE_KEY=''))


def test_bootstrap_enforces_production_configuration_and_api_has_health():
    assert 'production_config_errors' in APP
    bootstrap=APP.split('def bootstrap():',1)[1][:1800]
    assert 'production_config_errors' in bootstrap and 'RuntimeError' in bootstrap
    assert '@api.get("/health")' in API


def test_release_smoke_script_checks_core_pages_and_api():
    assert SMOKE.exists(); text=SMOKE.read_text(encoding='utf-8')
    for route in ['/', '/stays', '/store', '/api/v1/cities', '/api/v1/properties', '/api/v1/health']:
        assert route in text
    assert 'timeout=5' in text or 'timeout = 5' in text


def test_release_playwright_has_viewports_keyboard_reduced_motion_overflow_and_metadata():
    assert E2E.exists(); text=E2E.read_text(encoding='utf-8')
    for size in ['390', '844', '768', '1024', '1440', '900']:
        assert size in text
    assert 'reducedMotion' in text
    assert 'keyboard.press' in text
    assert 'scrollWidth' in text
    assert "rel='canonical'" in text or 'rel="canonical"' in text or "locator('link[rel=canonical]')" in text


def test_consumer_has_usable_not_found_page_and_render_has_plan5_security_envs():
    assert NOT_FOUND.exists()
    text=NOT_FOUND.read_text(encoding='utf-8')
    assert 'Page not found' in text and 'href="/"' in text
    for key in ['LIVENZA_ENV','CUSTOMER_AUTH_TEST_MODE','LIVENZA_PRIVATE_BUCKET','RAZORPAY_WEBHOOK_SECRET']:
        assert f'key: {key}' in RENDER


def test_env_example_documents_plan5_without_real_secrets():
    for key in ['LIVENZA_ENV','CUSTOMER_AUTH_TEST_MODE','SUPABASE_URL','SUPABASE_SERVICE_ROLE_KEY','LIVENZA_PRIVATE_BUCKET','LIVENZA_PUBLIC_BUCKET','LIVENZA_POSTDEPLOY_TOKEN']:
        assert f'{key}=' in ENV_EXAMPLE
    assert 'rzp_live_' not in ENV_EXAMPLE
    assert 'service-role' not in ENV_EXAMPLE
