[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidatePattern('^https://')]
  [string]$AppUrl,
  [string]$TaskName = 'LivenzaBackOfficeKiosk'
)

$ErrorActionPreference = 'Stop'
$edgeCandidates = @(
  "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
  "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe"
)
$edgePath = $edgeCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edgePath) { throw 'Microsoft Edge was not found. Install current Microsoft Edge first.' }

$arguments = "--kiosk `"$AppUrl`" --edge-kiosk-type=fullscreen --no-first-run --disable-pinch"
$action = New-ScheduledTaskAction -Execute $edgePath -Argument $arguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Days 3650) -RestartCount 5 -RestartInterval (New-TimeSpan -Minutes 1) -StartWhenAvailable
Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Description 'Launch Livenza Back Office in Microsoft Edge kiosk mode at Windows sign-in.' -Force | Out-Null

Write-Host "Livenza will open in Edge kiosk mode at sign-in for $env:USERNAME." -ForegroundColor Green
Write-Host 'For full Windows restriction, configure this Windows account under Settings > Accounts > Other users > Kiosk (Assigned Access), select Microsoft Edge, and use the same URL.' -ForegroundColor Yellow
Start-Process $edgePath -ArgumentList $arguments
