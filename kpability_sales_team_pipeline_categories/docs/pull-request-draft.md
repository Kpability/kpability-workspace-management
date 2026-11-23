# Draft PR: Add sales team pipeline categories

**Compare:** `feature/sales-team-pipeline-categories` → `20`

## Summary and scope

Add `kpability_sales_team_pipeline_categories` (`20.0.1.0.0`) as an optional
Odoo 20 add-on. Sales Managers explicitly map eligible categories on native sales
teams; the category form shows a read-only inverse. CRM filters the Category
dropdown by team/company and rejects invalid saves, imports and RPC changes
without silently replacing the category. Category-scoped quick-create exposes
Sales Team, and a read-only compatibility report helps managers find existing
mismatches without changing data or granting access.

- Only manifest dependency: `kpability_pipeline_categories` (merged PR #4).
  Native CRM roles, record rules and team/stage computations remain authoritative.
- No Studio, new security roles, inferred mappings or migration of existing
  leads. PR #7 and replacement categorized website/email intake (issue #6) are
  outside this diff. Review does not require merging PR #7 first.
- [Development plan](../../docs/development/sales-team-pipeline-categories.md)
  · [Configuration](../README.md)
  · [Verification and reproduction](sales-team-pipeline-categories.md)

## Test environment

Local Odoo `20.0+e`, Community `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`,
Enterprise `7773cfc038583d1b664491128424cd1904be946c`, Python 3.12.14 and
PostgreSQL 16.15. Base `20` at `c670310240a76e775afcdce3877db3f3ad40ac88`
includes CRM Stage Reasons `20.0.1.0.0`; category base `20.0.1.1.0`.
Browser: Playwright 1.65.0 / Chromium 158.0.8127.18 with `debug=assets`, with a
manager and a restricted salesperson. Multi-company boundaries are covered by
ORM tests, not a selected-company browser walkthrough.

## Verification and visuals

| Case | Expected and observed result | Evidence |
| --- | --- | --- |
| STPC01–02 | Mappings round-trip; inverse is read-only; unmapped categories do not appear. **Passed**, ORM + browser. | [Mapping](evidence/stpc01-team-mapping.png), [inverse](evidence/stpc01-read-only-inverse.png), [dropdown](evidence/stpc02-team-category-options.png) |
| STPC03, STPC06–07 | Native stage and Won/Lost behavior retained; category remains optional; used mappings and archived history protected. **Passed**, ORM. | [Cases and commands](sales-team-pipeline-categories.md#verification-record) |
| STPC04–05 | Incompatible saves, imports and RPC writes fail without changing the stored record. **Passed**, ORM + browser. | [Rejected save](evidence/stpc04-invalid-save.png) |
| STPC08 | Restricted salesperson sees the mapping read-only; backend denies writes and mapping grants no access. **Passed**, ORM + browser. | [Salesperson view](evidence/stpc08-sales-read-only.png) |
| STPC09–10 | Discard restores prior values; explicit save and reopen persist the new team/category; scoped quick-create retains the category. **Passed**, ORM + browser. | [After Discard](evidence/stpc09-after-discard.png), [after Save](evidence/stpc09-explicit-reclassification.png), [4.4-second recording](evidence/stpc09-save-discard.webm), [quick-create](evidence/stpc10-scoped-quick-create.png) |
| STPC11–12 | Report is read-only and rule-aware; optional engines not needed; install/update retain open, won, lost and unclassified CRM and audit dates. **Passed**, ORM, browser and lifecycle snapshots. | [Report](evidence/stpc11-read-only-report.png), [lifecycle results](sales-team-pipeline-categories.md#verification-record) |

Local totals: 37 fresh Odoo checks (35 authored), 35 after updating the add-on,
45 on a separate base-only install, and 7/7 Playwright cases, all passed.
Separately rehearsed upgrading the legacy website/email cleanup at PR #7 head
`b1f21eea6c1e8f0d3157d34e2856163dd36c49f9`: 8 website checks passed; stored
configuration and the unrelated native alias stayed intact. After installing
the team add-on, 35 STPC and 7/7 Playwright cases passed and CRM history stayed
unchanged. PR #7 was not merged into this branch.

## Release, rollback and review

No deployment, release tag or client adoption requested. Before enabling:

- [ ] PR #7 is approved and merged through `20`; on a staging copy upgrade the
  core and installed legacy companion without uninstalling. Smoke-test retired
  categorized routes, native routes and team CRM on the actual merged build.
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
