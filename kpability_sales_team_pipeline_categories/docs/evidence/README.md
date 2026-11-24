# Sales Team Pipeline Categories — local maker evidence

Synthetic data only. Captured November 23–24, 2026, using Playwright 1.65.0,
Chromium 158.0.8127.18 and Odoo `20.0+e` in `debug=assets` mode with Enterprise
web/CRM and CRM Stage Reasons installed. The seven browser tests passed on the
feature branch, including the merged PR #7 retirement and the writable
category-side mapping, without unexpected page JavaScript errors. Raw runs and
per-case videos are retained locally:

- `/tmp/opencode/kpability-stpc-final-browser/20261124080403/` (current branch)
- `/tmp/opencode/kpability-stpc-pr.t4szcPfV/browser-cleanup/20261123134557/`
  (earlier PR #7 retirement rehearsal; not the actual merged staging build)

| File | Case / observation |
| --- | --- |
| [`stpc01-team-mapping.png`](stpc01-team-mapping.png) | STPC01: native Sales Manager team configuration with explicit mappings |
| [`stpc01-category-team-mapping.png`](stpc01-category-team-mapping.png) | STPC01: Sales Manager adds a team from the category form; the Sales Teams tab shows the same relation after saving |
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
