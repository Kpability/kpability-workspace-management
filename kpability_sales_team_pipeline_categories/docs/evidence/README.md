# Sales Team Pipeline Categories — local maker evidence

Synthetic data only. Captured November 23–26, 2026, using Playwright 1.65.0,
Chromium 158.0.8127.18 and Odoo `20.0+e` in `debug=assets` mode with Enterprise
web/CRM and CRM Stage Reasons installed. All eight browser cases passed on
November 26, including the companyless-team case raised in PR #12. Raw runs
and per-case videos are retained locally:

- `/tmp/opencode/stpc-company-evidence.dyMouK8y/browser/20261126070050/` (November 26 run)
- `/tmp/opencode/kpability-stpc-final-browser/20261124080609/` (November 24 run)
- `/tmp/opencode/kpability-stpc-pr.t4szcPfV/browser-cleanup/20261123134557/`
  (earlier PR #7 retirement rehearsal; not the actual merged staging build)

| File | Case / observation |
| --- | --- |
| [`stpc01-team-mapping.png`](stpc01-team-mapping.png) | STPC01: native Sales Manager team configuration with explicit mappings |
| [`stpc01-category-team-mapping.png`](stpc01-category-team-mapping.png) | STPC01: Sales Manager adds a team from the category form; the Sales Teams tab shows the same relation after saving |
| [`stpc01-category-team-filter.png`](stpc01-category-team-filter.png) | STPC01: company-specific category picker offers only the same-company team; the wrong-company team is absent |
| [`stpc01-company-scope-excluded.png`](stpc01-company-scope-excluded.png) | STPC01: **1** Company is set; **2** the search for the companyless team returns no records. |
| [`stpc01-company-scope-shared.png`](stpc01-company-scope-shared.png) | STPC01: **1** Company is blank (shared); **2** the companyless team is mapped after save and reopen. |
| [`stpc01-company-scope-rejected.png`](stpc01-company-scope-rejected.png) | STPC01: **1** Company is set again; **2** the companyless team remains mapped; **3** Odoo rejects the save and preserves the shared mapping. |
| [`stpc02-team-category-options.png`](stpc02-team-category-options.png) | STPC02: team-mapped categories appear in the dropdown; the test asserts an unmapped category is absent |
| [`stpc04-invalid-save.png`](stpc04-invalid-save.png) | STPC04/STPC05: invalid team change rejected; an independent RPC attempt fails and the record stays unchanged |
| [`stpc08-sales-read-only.png`](stpc08-sales-read-only.png) | STPC08: salesperson sees mapping read-only; test also checks backend write denial |
| [`stpc09-after-discard.png`](stpc09-after-discard.png) | STPC09: Discard restores the original category and revenue before a second edit |
| [`stpc09-explicit-reclassification.png`](stpc09-explicit-reclassification.png) | STPC09: compatible team/category replacement and expected revenue persist after Save/reload |
| [`stpc09-save-discard.webm`](stpc09-save-discard.webm) | STPC09: 4.4-second automated recording, from dirty form to explicit save and reopen |
| [`stpc10-scoped-quick-create.png`](stpc10-scoped-quick-create.png) | STPC10: category-scoped board with a visible team selector and correctly categorized created card; the next draft still uses the native default |
| [`stpc11-read-only-report.png`](stpc11-read-only-report.png) | STPC11: manager report with no New button or row selectors; ORM/lifecycle tests separately cover real legacy mismatches in the synthetic dataset |

[`dataset.json`](dataset.json) records synthetic IDs, installed module versions,
browser/runtime version and executed cases; it contains no credentials. Use the
repeatable ORM, browser and lifecycle tests in the
[implementation record](../sales-team-pipeline-categories.md) for backend
authorization and upgrade safety.

No client data, real mailbox, remote deployment or independent checker approval
is represented by these files. The separate rehearsal is not verification of
the actual merged `20` staging build.
