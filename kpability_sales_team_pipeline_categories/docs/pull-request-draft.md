# Draft PR: Add sales team pipeline categories

**Compare:** `feature/sales-team-pipeline-categories` → `20`

## Summary and scope

Add `kpability_sales_team_pipeline_categories` (`20.0.1.0.0`) as an optional
Odoo 20 add-on. Sales Managers explicitly map eligible categories on native sales
teams; the category form offers the same editable mapping from the category
side (read-only for non-managers), with team-side protections still enforced.
CRM filters the Category
dropdown by team/company and rejects invalid saves, imports and RPC changes
without silently replacing the category. Category-scoped quick-create exposes
Sales Team, and a read-only compatibility report helps managers find existing
mismatches without changing data or granting access.

- Only manifest dependency: `kpability_pipeline_categories` (merged PR #4).
  Native CRM roles, record rules and team/stage computations remain authoritative.
- No Studio, new security roles, inferred mappings or migration of existing
  leads. PR #7 is merged into this branch; replacement categorized website/email
  intake (issue #6) remains outside this diff.
- [Development plan](../../docs/development/sales-team-pipeline-categories.md)
  · [Configuration](../README.md)
  · [Verification and reproduction](sales-team-pipeline-categories.md)

## Test environment

Local Odoo `20.0+e`, Community `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`,
Enterprise `7773cfc038583d1b664491128424cd1904be946c`, Python 3.12.14 and
PostgreSQL 16.15. Branch includes `origin/20` at
`80bbe6b78ee465fc8e1453082d57768e052cf81e` (PR #7 retirement merged); category
base updates to `20.0.1.2.0`, the installed website companion
to `20.0.1.1.0`, and CRM Stage Reasons remains `20.0.1.0.0`.
Browser: Playwright 1.65.0 / Chromium 158.0.8127.18 with `debug=assets`, with a
manager and a restricted salesperson. Multi-company boundaries are covered by
ORM tests, not a selected-company browser walkthrough.

## Verification and visuals

| Case | Expected and observed result | Evidence |
| --- | --- | --- |
| STPC01–02 | Mappings round-trip from both configuration forms; category-side removals still enforce used-history and company protections; unmapped categories do not appear. **Passed**, ORM + browser. | [Mapping](evidence/stpc01-team-mapping.png), [category-side mapping](evidence/stpc01-category-team-mapping.png), [dropdown](evidence/stpc02-team-category-options.png) |
| STPC03, STPC06–07 | Native stage and Won/Lost behavior retained; category remains optional; used mappings and archived history protected. **Passed**, ORM. | [Cases and commands](sales-team-pipeline-categories.md#verification-record) |
| STPC04–05 | Incompatible saves, imports and RPC writes fail without changing the stored record. **Passed**, ORM + browser. | [Rejected save](evidence/stpc04-invalid-save.png) |
| STPC08 | Restricted salesperson sees the mapping read-only; backend denies writes and mapping grants no access. **Passed**, ORM + browser. | [Salesperson view](evidence/stpc08-sales-read-only.png) |
| STPC09–10 | Discard restores prior values; explicit save and reopen persist the new team/category; scoped quick-create retains the category. **Passed**, ORM + browser. | [After Discard](evidence/stpc09-after-discard.png), [after Save](evidence/stpc09-explicit-reclassification.png), [4.4-second recording](evidence/stpc09-save-discard.webm), [quick-create](evidence/stpc10-scoped-quick-create.png) |
| STPC11–12 | Report is read-only and rule-aware; optional engines not needed; install/update retain open, won, lost and unclassified CRM and audit dates. **Passed**, ORM, browser and lifecycle snapshots. | [Report](evidence/stpc11-read-only-report.png), [lifecycle results](sales-team-pipeline-categories.md#verification-record) |

Final combined branch, fresh Enterprise demo and no-demo databases: **90 Odoo
checks, 0 failed, 0 errors each**; **7/7 Playwright cases passed**. The final
run includes the merged PR #7 retirement, category-side mapping, category base
`20.0.1.2.0`, website companion `20.0.1.1.0`, Stage Reasons and keyword
assignment. Earlier foundations were also verified at 37 fresh (35 authored),
35 update and 45 base-only checks; the separate PR #7 rehearsal covered 8
website checks, retained stored configuration and the unrelated native alias,
and passed 35 STPC plus 7/7 browser checks after installing the team add-on.
Those historical runs remain in the implementation record.

## Release, rollback and review

No deployment, release tag or client adoption requested. Before enabling:

- [ ] PR #7 is merged through `20` and this branch is rebased/merged as needed;
  on a staging copy upgrade the core and installed legacy companion without
  uninstalling. Smoke-test retired categorized routes, native routes and team
  CRM on the actual merged build.
- [ ] An independent checker reproduces the mapping, rejected save/RPC, native
  salesperson permissions, Save/Discard, quick-create and compatibility report
  (including selected-company switching). Access owner approves the intended
  mappings and access. Review each target company's existing incompatibilities.
- [ ] Rehearse restoring a matching database/filestore/code backup. If routing
  or access checks fail, stop adoption and use an approved restore or forward
  fix; uninstall alone is not a rollback.

Maker verification is local only. Independent sign-off, Odoo.sh/client UAT,
external mailbox delivery, production-volume profiling and optional rule-engine
integration were not run. See [release gates and inherited risks](sales-team-pipeline-categories.md#outstanding-release-gates).
