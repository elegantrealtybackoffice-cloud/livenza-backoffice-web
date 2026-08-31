LIVENZA BACKOFFICE — FULL SUITE RECONCILIATION — 2026-08-31

Purpose
- Restore the dynamic Tesla OS Dock and all existing suite entries.
- Keep Staff Salary Studio fully installed.
- Restore runtime modules that are tracked by current main but physically missing from the uploaded repository folder.
- Preserve the current backoffice startup gate fix (consumer platform disabled unless explicitly enabled).

Verified suite registry
Home, Agreement Studio, Landlord Master, Tenant Master, Rooms, Residents, Queries,
Reviews, Video Wall, Food, Billing, Banking, Staff Salary Studio, Electricity,
WhatsApp, Email, Drive, Letterhead Studio, Livenza Vault, System Settings.

Deployment
1. Extract this ZIP.
2. Copy ALL files/folders inside it into the ROOT of livenza-backoffice-web.
3. Preserve the folder structure and choose Replace when Windows asks.
4. Do NOT delete any other repository files.
5. In GitHub Desktop, confirm the changed files, commit:
   Reconcile all backoffice suites and Staff Salary Studio
6. Push origin. Render Auto-Deploy should run.
7. Do NOT rerun the Staff Salary SQL migrations; they were already applied to Supabase.
8. Do NOT deploy any of the earlier Staff Salary repair ZIPs after this package.

What was corrected
- templates/base.html: dynamic Dock restored via appgroups.render_dock_apps().
- app.py: dashboard receives lightweight_dock_apps(user); legacy Landlord Master,
  Tenant Master and Livenza Vault registry entries restored; Staff Salary retained.
- templates/_application_groups.html: Staff Salary retained in Finance and command search.
- 19 livenza_*.py runtime modules included as one consistent set.

After deploy
- Sign in as Admin.
- Confirm all suite icons appear in the Dock.
- Open Suites and test Agreement, Rooms, Queries, Billing, Banking, Staff Salary,
  Electricity, Video Wall, Food, Letterhead, Vault and Settings.
- External WhatsApp/Email/Drive functions still require their own integration configuration.
