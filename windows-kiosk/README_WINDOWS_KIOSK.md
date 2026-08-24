# Livenza Windows kiosk setup

## 1. Enable automatic launch

Open Windows PowerShell as the Windows user that will run Livenza, then run:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\Enable-LivenzaKiosk.ps1 -AppUrl "https://YOUR-LIVENZA-SITE.example"
```

This creates a per-user scheduled task that opens Microsoft Edge in full-screen kiosk mode whenever that user signs in.

## 2. Lock the rest of Windows

Automatic launch is not a full Windows security boundary. For that, sign in as a Windows administrator and open:

**Settings > Accounts > Other users > Kiosk > Get started**

Create/select a dedicated standard local user, choose Microsoft Edge, select a full-screen/single-app experience, and enter the Livenza HTTPS URL. This is Windows Assigned Access. Keep a separate administrator account for maintenance.

The secure attention sequence (Ctrl+Alt+Delete) remains controlled by Windows. A website should not and cannot override it.

## 3. Enable the Livenza PIN gate

In Livenza, open **Admin > Kiosk & Main Screen**, set a PIN of at least six characters, enter the administrator password, and enable the lock. The server then rejects access to all authenticated Livenza pages until the kiosk PIN or the signed-in user's password is entered.

## Disable

Run `Disable-LivenzaKiosk.ps1` for startup removal, turn off the Livenza PIN gate in Admin, and remove Assigned Access from Windows Settings if it was configured.

Reference: <https://learn.microsoft.com/windows/configuration/assigned-access/>
