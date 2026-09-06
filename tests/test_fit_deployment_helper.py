from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / 'scripts' / 'deploy_livenza_fit.sh'
PS1 = ROOT / 'scripts' / 'Deploy-LivenzaFit.ps1'


def test_fit_deploy_helper_files_exist():
    assert SCRIPT.exists(), 'missing bash deployment helper'
    assert PS1.exists(), 'missing PowerShell deployment helper'


def test_fit_deploy_helper_dry_run_orders_safe_gates():
    result = subprocess.run(
        ['bash', str(SCRIPT), '--dry-run', '--full'],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    output = result.stdout
    assert 'python -m pytest -q' in output
    assert 'tsc -p web/tsconfig.fit-domain.json --pretty false' in output
    assert 'node --test tests/fit-*.test.cjs' in output
    assert 'npm run lint' in output
    assert 'npm run build' in output
    assert 'npm run check:bundle' in output
    assert 'npm run test:e2e' in output
    assert 'psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/livenza_fit_v1.sql' in output
    assert output.index('python -m pytest -q') < output.index('psql "$DATABASE_URL"')
    assert output.index('psql "$DATABASE_URL"') < output.index('npm run build')


def test_fit_deploy_helper_refuses_real_migration_without_database_url():
    result = subprocess.run(
        ['bash', str(SCRIPT), '--migrate'],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
        env={'PATH': '/usr/bin:/bin'},
    )
    assert result.returncode != 0
    assert 'DATABASE_URL is required' in result.stdout


def test_powershell_helper_has_same_safety_contract():
    text = PS1.read_text(encoding='utf-8')
    assert '[switch]$DryRun' in text
    assert '[switch]$Migrate' in text
    assert '[switch]$Full' in text
    assert 'DATABASE_URL' in text
    assert 'livenza_fit_v1.sql' in text
    assert 'npm run build' in text
    assert 'npm run test:e2e' in text


def test_full_deploy_installs_web_toolchain_before_typescript_checks():
    text = SCRIPT.read_text(encoding='utf-8')
    assert 'web/node_modules/.bin/tsc' in text
    result = subprocess.run(
        ['bash', str(SCRIPT), '--dry-run', '--full'],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    assert result.returncode == 0, result.stdout
    output = result.stdout
    assert 'cd web && npm install --no-audit --no-fund' in output
    assert output.index('cd web && npm install --no-audit --no-fund') < output.index('tsconfig.fit-domain.json')
