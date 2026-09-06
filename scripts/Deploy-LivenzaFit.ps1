param(
  [switch]$DryRun,
  [switch]$Verify,
  [switch]$Migrate,
  [switch]$Full
)

$ErrorActionPreference = 'Stop'
$Root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $Root

$modeCount = @($Verify, $Migrate, $Full | Where-Object { $_ }).Count
if ($modeCount -ne 1) {
  throw 'Choose exactly one of -Verify, -Migrate, or -Full.'
}

$required = @('app.py', 'web/package.json', 'migrations/livenza_fit_v1.sql', 'web/src/app/fit/page.tsx')
foreach ($item in $required) {
  if (-not (Test-Path $item)) { throw "Not a compatible Livenza.life repository: missing $item" }
}

function Invoke-Step([string]$Command) {
  Write-Host "+ $Command"
  if (-not $DryRun) {
    & cmd.exe /d /s /c $Command
    if ($LASTEXITCODE -ne 0) { throw "Command failed ($LASTEXITCODE): $Command" }
  }
}

function Get-TscCommand {
  $localTsc = 'web\node_modules\.bin\tsc.cmd'
  if ($DryRun -or (Test-Path $localTsc)) { return $localTsc }
  $globalTsc = Get-Command tsc -ErrorAction SilentlyContinue
  if ($globalTsc) { return 'tsc' }
  throw 'TypeScript compiler not found. Run npm install in web/ or use -Full.'
}

function Invoke-WebInstall {
  Invoke-Step 'cd web && npm install --no-audit --no-fund'
}

function Invoke-Verify {
  $tsc = Get-TscCommand
  Invoke-Step 'python -m pytest -q'
  Invoke-Step "$tsc -p web/tsconfig.fit-domain.json --pretty false"
  Invoke-Step 'node --test tests/fit-*.test.cjs'
  Invoke-Step "$tsc -p web/tsconfig.offline.json --pretty false"
  Invoke-Step "$tsc -p web/tsconfig.fit-ui.json --pretty false"
  Invoke-Step 'python -m py_compile app.py livenza_customer_core.py livenza_api_v1.py'
  Invoke-Step 'cd web && node scripts/check-route-sources.mjs'
  Invoke-Step 'node --check web/public/fit-sw.js'
  Invoke-Step 'python -m json.tool web/public/fit.webmanifest >NUL'
}

function Invoke-Migration {
  if (-not $DryRun -and [string]::IsNullOrWhiteSpace($env:DATABASE_URL)) {
    throw 'DATABASE_URL is required for -Migrate/-Full. Refusing to guess a database.'
  }
  Invoke-Step 'psql "%DATABASE_URL%" -v ON_ERROR_STOP=1 -f migrations/livenza_fit_v1.sql'
}

function Invoke-WebGates {
  Invoke-Step 'cd web && npm test -- --run'
  Invoke-Step 'cd web && npm run lint'
  Invoke-Step 'cd web && npm run build'
  Invoke-Step 'cd web && npm run check:bundle'
  Invoke-Step 'cd web && npm run test:e2e'
}

if ($Verify) { Invoke-Verify }
elseif ($Migrate) { Invoke-Migration }
else {
  Invoke-WebInstall
  Invoke-Verify
  Invoke-Migration
  Invoke-WebGates
}

Write-Host 'Livenza.fit deployment helper completed the requested gates.'
