[CmdletBinding()]
param([string]$TaskName = 'LivenzaBackOfficeKiosk')

$ErrorActionPreference = 'Stop'
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host 'Livenza automatic kiosk startup has been disabled.' -ForegroundColor Green
} else {
  Write-Host 'No Livenza kiosk startup task was found.' -ForegroundColor Yellow
}
Write-Host 'If Windows Assigned Access is enabled, remove that kiosk assignment separately in Settings > Accounts > Other users > Kiosk.'
