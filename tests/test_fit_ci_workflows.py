from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CI = ROOT / ".github" / "workflows" / "livenza-fit-ci.yml"
STAGING = ROOT / ".github" / "workflows" / "livenza-fit-staging.yml"


def test_fit_ci_workflow_exists_and_runs_required_quality_gates():
    assert CI.exists(), "missing Livenza.fit CI workflow"
    text = CI.read_text(encoding="utf-8")
    assert "pull_request:" in text
    assert "push:" in text
    assert "actions/setup-python" in text
    assert "actions/setup-node" in text
    assert "python -m pytest -q" in text
    assert "node --test tests/fit-*.test.cjs" in text
    assert "npm install --no-audit --no-fund" in text
    assert text.index("npm install --no-audit --no-fund") < text.index("tsc -p web/tsconfig.fit-domain.json")
    assert "npm run lint" in text
    assert "npm run build" in text
    assert "npm run check:bundle" in text
    assert "DATABASE_URL" not in text, "PR CI must never touch a database"


def test_fit_staging_workflow_is_manual_and_environment_guarded():
    assert STAGING.exists(), "missing Livenza.fit staging workflow"
    text = STAGING.read_text(encoding="utf-8")
    assert "workflow_dispatch:" in text
    assert "environment: staging" in text
    assert "secrets.LIVENZA_STAGING_DATABASE_URL" in text
    assert "scripts/deploy_livenza_fit.sh --full" in text
    assert "pull_request:" not in text
    assert "push:" not in text
