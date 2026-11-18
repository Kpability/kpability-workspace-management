# Sales Team Pipeline Categories — local maker evidence

Synthetic data only. Captured November 13, 2026, using Playwright 1.65.0,
Chromium 158.0.8127.18 and verified Odoo `20.0+e` with both Enterprise web and CRM
installed. The complete seven-case browser run passed without unexpected page
JavaScript errors. The raw run and per-case videos are retained at:

`/tmp/opencode/kpability-stpc-browser/20261113024544/`

| File | Case / observation |
| --- | --- |
| `stpc01-team-mapping.png` | STPC01: native Sales Manager team configuration with explicit mappings |
| `stpc01-read-only-inverse.png` | STPC01: read-only category-to-team inverse |
| `stpc04-invalid-save.png` | STPC04/STPC05: invalid team change rejected; RPC independently confirms persisted classification is unchanged |
| `stpc09-explicit-reclassification.png` | STPC09: explicit compatible team/category replacement and expected revenue persist after Save/reload |
| `stpc09-save-discard.webm` | STPC09: unsaved changes leave CRM unchanged, Discard restores originals, then explicit compatible Save succeeds |
| `stpc10-scoped-quick-create.png` | STPC10: category-scoped board with a visible team selector and correctly categorized created card; native next draft can still have an incompatible default and warns without blocking correction |
| `stpc08-sales-read-only.png` | STPC08: salesperson sees mapping read-only; test also checks backend write denial |
| `stpc11-read-only-report.png` | STPC11: manager report with no New button or row selectors; ORM/lifecycle tests separately cover genuine pre-install legacy rows and no report mutations |

`dataset.json` records synthetic IDs, browser/runtime version and executed cases;
it contains no credentials. Do not treat screenshots alone as proof of backend
authorization or upgrade safety: use the repeatable ORM, browser and lifecycle
tests described in the [implementation record](../sales-team-pipeline-categories.md).

No client data, real mailbox, remote deployment or independent checker approval
is represented by these files. The separate website/email restoration remains
gated on PR #7's approved merge.
