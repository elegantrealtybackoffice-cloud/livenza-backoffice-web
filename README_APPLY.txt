Livenza.life Meta Legal Pages Update
Date: 2026-09-02
Source commit: abb63ea3d067a9a9220d92d45f9e4dad4a70bd68

Adds only new files. It does not overwrite existing header/footer, OTP, API, booking, store, or deployment files.

Routes added:
- /privacy
- /terms
- /data-deletion

Recommended Git method on the latest main branch:
  git apply 0001-Add-Meta-compliant-Livenza-legal-pages.patch
or cherry-pick the commit if the branch/commit is imported into the same repository.

Verification performed before packaging:
- 23 relevant Python source/contract tests passed
- offline TypeScript check passed
- git diff --check passed

A real Next.js production build could not be run in this environment because node_modules are not available here. Run npm ci && npm run build on your normal CI/Render pipeline before production cutover.
