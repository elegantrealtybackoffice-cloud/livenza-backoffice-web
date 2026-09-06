#!/usr/bin/env bash
set -euo pipefail

DRY_RUN=0
VERIFY=0
MIGRATE=0
FULL=0

usage() {
  cat <<'EOF'
Livenza.fit deployment helper

Usage:
  scripts/deploy_livenza_fit.sh --verify
  scripts/deploy_livenza_fit.sh --migrate
  scripts/deploy_livenza_fit.sh --full
  scripts/deploy_livenza_fit.sh --dry-run --full

Modes:
  --verify   Run portable source verification only.
  --migrate  Apply only migrations/livenza_fit_v1.sql to DATABASE_URL.
  --full     Install web tooling, run verification, migrate, then production web gates.
  --dry-run  Print commands without executing them.
EOF
}

for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --verify) VERIFY=1 ;;
    --migrate) MIGRATE=1 ;;
    --full) FULL=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $arg" >&2; usage; exit 2 ;;
  esac
done

if (( VERIFY + MIGRATE + FULL == 0 )); then
  usage
  exit 2
fi

if (( VERIFY + MIGRATE + FULL > 1 )); then
  echo "Choose only one of --verify, --migrate, or --full." >&2
  exit 2
fi

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

for required in app.py web/package.json migrations/livenza_fit_v1.sql web/src/app/fit/page.tsx; do
  if [[ ! -f "$required" ]]; then
    echo "Not a compatible Livenza.life repository: missing $required" >&2
    exit 3
  fi
done

run_shell() {
  local command="$1"
  echo "+ $command"
  if (( ! DRY_RUN )); then
    bash -lc "$command"
  fi
}

run_web_install() {
  run_shell 'cd web && npm install --no-audit --no-fund'
}

resolve_tsc() {
  if (( DRY_RUN )); then
    printf '%s\n' 'web/node_modules/.bin/tsc'
  elif [[ -x web/node_modules/.bin/tsc ]]; then
    printf '%s\n' 'web/node_modules/.bin/tsc'
  elif command -v tsc >/dev/null 2>&1; then
    command -v tsc
  else
    echo 'TypeScript compiler not found. Run npm install in web/ or use --full.' >&2
    exit 5
  fi
}

run_verify() {
  local tsc_bin
  tsc_bin="$(resolve_tsc)"
  run_shell 'python -m pytest -q'
  run_shell "$tsc_bin -p web/tsconfig.fit-domain.json --pretty false"
  run_shell 'node --test tests/fit-*.test.cjs'
  run_shell "$tsc_bin -p web/tsconfig.offline.json --pretty false"
  run_shell "$tsc_bin -p web/tsconfig.fit-ui.json --pretty false"
  run_shell 'python -m py_compile app.py livenza_*.py'
  run_shell 'cd web && node scripts/check-route-sources.mjs'
  run_shell 'node --check web/public/fit-sw.js'
  run_shell 'python -m json.tool web/public/fit.webmanifest >/dev/null'
}

run_migration() {
  if (( ! DRY_RUN )) && [[ -z "${DATABASE_URL:-}" ]]; then
    echo 'DATABASE_URL is required for --migrate/--full. Refusing to guess a database.' >&2
    exit 4
  fi
  run_shell 'psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f migrations/livenza_fit_v1.sql'
}

run_web_gates() {
  run_shell 'cd web && npm test -- --run'
  run_shell 'cd web && npm run lint'
  run_shell 'cd web && npm run build'
  run_shell 'cd web && npm run check:bundle'
  run_shell 'cd web && npm run test:e2e'
}

if (( VERIFY )); then
  run_verify
elif (( MIGRATE )); then
  run_migration
else
  run_web_install
  run_verify
  run_migration
  run_web_gates
fi

echo 'Livenza.fit deployment helper completed the requested gates.'
