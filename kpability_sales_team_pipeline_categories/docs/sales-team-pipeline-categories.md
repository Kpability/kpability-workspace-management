# Sales Team Pipeline Categories — implementation record

## Scope and approved policies

Implementation began November 13, 2026 on the existing
`feature/sales-team-pipeline-categories` branch after incorporating approved
`origin/20` at `cf54708dd35761c9a3e09d27a0bb2aa711f4b378` (merged PR #4).
The November 24 update incorporates `origin/20` at
`80bbe6b` (PR #7 legacy-intake retirement merged) and adds category-side team
mapping while keeping one authoritative relation. The add-on is independently
reviewable; the retirement upgrade and a merged staging smoke test remain
rollout gates, not manifest dependencies.

Approved policies replace the old proposal in `docs/development/`:

| Decision | Implemented policy |
| --- | --- |
| Cardinality | One authoritative `crm.team.pipeline_category_ids` M2M; editable `crm.pipeline.category.sales_team_ids` inverse on `crm_team_pipeline_category_rel(team_id,category_id)`, with category-side edits routed through the team field and its protections |
| Empty/missing team | No new categorized assignments; unclassified native CRM remains possible |
| Defaults | No automatic category, inferred mapping or backfill |
| Company | Companyless teams map only shared categories; company-specific teams map shared/own-company categories; CRM access/company rules still apply |
| Incompatible edits | Preserve category; require explicit compatible replacement/clear; native stage recomputation remains native |
| History | All records protect used mappings, including archived/Won/Lost/hidden records; unrelated historical edits remain allowed |
| Security | Native Sales Manager editing, existing ACLs/rules, no visibility grants; existence-only elevated integrity checks with generic errors |
| Intake | Deferred; the new optional intake modules and explicit recovery are not implemented in this foundation delivery |

## References and naming

All four PDFs in `docs/references/` were reread before implementation:
`Standard Implementation Considerations with Timelinepdf.pdf` is the explicit
ownership/naming baseline; the two Standardization notes provide context; Odoo
Submodules defines reusable central modules and independently approved client
adoption. No Studio, client-specific constants, production data or new role
system is introduced. Thirdy's RBAC/menus/global Save/Discard and TJ's territory,
reasons/templates remain outside this feature.

Use descriptive snake_case fields and PascalCase classes. Preserve native and
approved base field names. New relational fields use conventional `*_id/*_ids`;
booleans retain conventional names. Future new scalar fields must use `s_`, `n_`,
`e_`, `j_`, `d_`, `dt_`, `ts_` as specified. No new scalar fields are required by
this foundation. Business choices are records, not hard-coded selections.

## Verified source baseline

| Component | Revision / requirement |
| --- | --- |
| Target branch, `20` | `80bbe6b` on November 24, 2026, after the PR #7 retirement merge; feature branch includes this merge |
| Official Odoo Community source, `20.0` | `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`, sibling `../odoo`, official GitHub origin |
| Official Enterprise source, `20.0` | `7773cfc038583d1b664491128424cd1904be946c`, sibling `../enterprise`, official GitHub origin |
| Python | CPython 3.12.14; target source supports 3.12–3.14 |
| PostgreSQL | PostgreSQL 16.15, dedicated disposable local container on loopback |
| Edition | Runtime `20.0+e`, with `web_enterprise` and `crm_enterprise` installed; browser setup asserts both edition and modules |
| Add-ons | Team consumer `20.0.1.0.0` (LGPL-3), category base `20.0.1.2.0`, website companion `20.0.1.1.0` when installed, CRM Stage Reasons `20.0.1.0.0`, keyword assignment `20.0.1.1.0` |

Native APIs inspected: stored/precomputed team selection, user-driven team
recomputation, computed company and stage, CRM `create/write`, native
`_handle_salesmen_assignment`, conversion/merge/Won/Lost, team company/member
constraints, and supported inherited views. New CRM validation compares final
computed category/team/company/stage, not just submitted values. There is no
public bypass context flag. It runs for creation and changed routing/stages;
unchanged historical routing is not retroactively rejected on unrelated writes.

## Read-only rollout report

The manager-only action computes a normal ORM domain from visible category/team
configuration, including archived mappings. It lists missing team/category
mappings, incompatible category/team/record company scopes and incompatible
category stages. The report's list/form disable editing, record selection and
mutating action menus using isolated native-view registrations; ordinary CRM
views are unchanged. Calling it creates no records and changes no audit dates.
Normal CRM record rules still filter rows.
It intentionally does not classify archived teams/categories themselves as bad
historical references. Opening it under restricted companies is not a global
compatibility certificate. Native team-specific stage restrictions remain the
base category module's responsibility.

Configuration removal checks use only narrowly elevated, `active_test=False`,
`search_count(..., limit=1)` existence checks. The report never uses `sudo`.
Mappings are not authorization. Unrelated legacy invalid pairs do not prevent
incrementally adding correct mappings; only removing used pairs or invalidating
company scope is blocked.

## Reproduce on disposable local databases

Supply connection settings externally. Stop a server before updating **its**
database. Never use a client database or reuse the separate cleanup worktree's
running database. Example from the repository root:

```bash
/tmp/opencode/kpability-odoo20-venv/bin/python ../odoo/odoo-bin \
  --addons-path="../enterprise,../odoo/addons,$PWD" \
  --db_host=127.0.0.1 --db_port=55421 --db_user=odoo \
  --database=kpability_pipeline_stpc_pr_fresh \
  --init=kpability_sales_team_pipeline_categories,crm_stage_reasons,web_enterprise,crm_enterprise \
  --without-demo=True --test-enable \
  --test-tags=/kpability_sales_team_pipeline_categories \
  --stop-after-init --http-interface=127.0.0.1 --http-port=18030 \
  --data-dir=/tmp/opencode/kpability-stpc-data
```

Supply the database credential through `PGPASSWORD` rather than the command line.
For same-version upgrade, use `--update=kpability_sales_team_pipeline_categories`
instead of `--init`. Run the existing base suite on a **separate base-only**
database. Its old fixtures intentionally lack team mappings and cannot simply
be treated as valid categorized input after installing this stricter consumer.
The new suite tests both add-ons together with explicitly configured team
fixtures and native CRM flows. It does not retrofit automatic mapping into
production or the old test suite.

Run the separate browser runner only after starting the server against its
disposable database, with credentials provided externally:

```bash
ODOO_E2E_ALLOW_WRITES=1 \
ODOO_E2E_DEBUG_ASSETS=1 \
ODOO_E2E_URL=http://127.0.0.1:18030 \
ODOO_E2E_DATABASE=kpability_pipeline_stpc_pr_fresh \
ODOO_E2E_PASSWORD="$ODOO_TEST_ADMIN_PASSWORD" \
uv run --no-project --with playwright==1.65.0 python \
  kpability_sales_team_pipeline_categories/tests/e2e/test_sales_team_pipeline_categories.py
```

Install the matching Playwright Chromium first if it is not already cached.
The runner rejects non-local URLs, non-STPC database names and missing explicit
write opt-in. Synthetic records remain for inspection. Screenshots, per-case
videos and a non-secret dataset manifest are written under
`/tmp/opencode/kpability-stpc-browser/<run-id>/` by default.

`tests/check_lifecycle.py` is a separate `odoo-bin shell` input, not an Odoo
test-loader module. To reproduce preservation checks on a **new base-only**
`kpability_pipeline_stpc_*` database:

1. Install only the category base plus Enterprise, without the team consumer.
2. Supply `ODOO_E2E_ALLOW_WRITES=1`,
   `ODOO_STPC_LIFECYCLE_SNAPSHOT=/tmp/opencode/<unique-name>.json` and
   `ODOO_STPC_LIFECYCLE_MODE=seed`; pass the script on shell stdin.
3. Stop that database's server and install the team consumer.
4. Run the script with mode `after_install`. It verifies exact CRM/configuration
   snapshots and audit dates, checks the report and absence of inferred mappings,
   then makes one **explicit synthetic** mapping decision.
5. Update the consumer with the server stopped; run mode `after_update` to verify
   exact record preservation and retention of that explicit mapping.

Use the same addons path, database and snapshot for all phases. The script refuses
to overwrite an existing baseline or use a snapshot outside `/tmp/opencode`.

## Verification record

Re-run locally on November 23–24, 2026, on the source/runtime baseline above.
Raw maker logs are local under `/tmp/opencode/`.

| Run | Result | File in the local run directory |
| --- | --- | --- |
| Final combined branch with `20` at `80bbe6b` (PR #7 retirement included), fresh Enterprise demo database, all tagged suites | **90 checks, 0 failed, 0 errors** | `kpability-stpc-final-1534c71.log` |
| Same final branch, fresh no-demo database, same tagged suites | **90 checks, 0 failed, 0 errors** | `kpability-stpc-final-nodemo.log` |
| Same final branch, Playwright `debug=assets`, category-side mapping included | **7/7 passed**, no unexpected page JavaScript errors | `kpability-stpc-final-browser.log`, `browser/20261124080609/` |
| Fresh consumer + Enterprise + CRM Stage Reasons, no website companion | **37 passed**, including all 35 authored STPC methods | `fresh.log` |
| Same-version consumer update on the fresh database | **35 passed** | `fresh-update.log` |
| Category base + Enterprise, no team consumer | **45 passed**, including 43 authored base tests | `base-only.log` |
| Consumer install/update on a database with existing CRM history | **Passed**: open, won, lost and unclassified CRM, categories, stages and audit dates unchanged; no inferred mapping; explicit mapping retained through update | `lifecycle-lifecycle.log` |
| Playwright `debug=assets` against the branch alone | **7/7 passed**, no unexpected page JavaScript errors | `fresh-browser.log`, `browser-fresh/` |
| Separate cleanup upgrade before installing the consumer | **8 website checks passed**; legacy configuration retained and only the owned categorized alias retired | `cleanup-upgrade.log`, `cleanup-intake.log` |
| Consumer installed after cleanup upgrade | **35 STPC checks and 7/7 browser tests passed**; CRM snapshot and retained intake configuration unchanged | `cleanup-team-install.log`, `cleanup-lifecycle.log`, `cleanup-browser.log`, `browser-cleanup/` |

Browser runner: Playwright 1.65.0, Chromium 158.0.8127.18, Odoo `20.0+e`.
The first intake snapshot check mistakenly compared a relation display name
that changes when the owned alias is retired. The corrected check compares
stored relation IDs and was run both before and after installing the team
consumer. The unrelated native alias was checked including its audit timestamp.
Historical PR #4/#7 results are not counted in the table.

| Cases | Authored coverage |
| --- | --- |
| STPC01 | M2M round-trip and category-side editing, authoritative-side protections including sudo/RPC, copy behavior |
| STPC02 | Draft team-dependent options, active mapping eligibility, no hidden defaults |
| STPC03 | Category/native team stage intersection, scoped board columns, native bulk Won/Lost/restore |
| STPC04 | Compatible and rejected team changes, explicit reclassification/clear, native stage recompute, non-blocking warning |
| STPC05 | ORM/RPC/context-spoof rejection, atomic batch create/write, actual `load` import |
| STPC06 | Missing team/empty mapping, unclassified CRM, no starter mapping, shared/companyless rules |
| STPC07 | All-history removal protections, archived mappings, hidden-company existence checks, company changes and team deletion |
| STPC08 | Native manager versus salesperson permissions, no record-access grants, company restrictions |
| STPC09 | Unsaved form preservation, native Discard and explicit Save/reclassification |
| STPC10 | Visible quick-create team, conversion, duplicate, matching-category merge, native assignment and salesperson-driven recompute |
| STPC11 | Read-only legacy report, incremental mapping, selected-company filtering, second-company reuse, install/update snapshots |
| STPC12 | Only the category prerequisite; native inherited views; optional rule/dropdown engines absent |

Curated synthetic screenshots/video and their case mapping are in
[`evidence/README.md`](evidence/README.md). Local maker evidence is not independent
checker approval, a full native CRM suite, or Odoo.sh/client UAT certification.

## Reproduce the separate PR #7 rehearsal

Use a separate synthetic database and a separate, disposable source tree. The
rehearsal integrated PR #7 head `b1f21eea6c1e8f0d3157d34e2856163dd36c49f9`
with feature source `c5015546d4de1e65e015122b07519533c007986f` (no changes to
the feature's production code). That rehearsal did **not** merge PR #7 into the
feature branch. The November 24 branch update later merged the approved `20`
head, including PR #7, as recorded above.

1. With approved base code, install category base `20.0.1.1.0` and legacy
   website companion `20.0.1.0.0` alongside Enterprise and CRM Stage Reasons.
   Leave the team consumer uninstalled. Seed and snapshot representative CRM
   history, a category's website mapping, its owned alias, and an unrelated
   native CRM alias. Use a reserved synthetic domain such as `example.test`.
2. On the integrated code, update `kpability_pipeline_categories` to
   `20.0.1.2.0` and `kpability_website_pipeline_categories` to `20.0.1.1.0`.
   Do not uninstall either module. Run the website companion suite
   (`--test-enable --test-tags=/kpability_website_pipeline_categories`).
   Verify stored website/alias configuration remains; the old form displays the
   retirement message; only the categorized alias name is disabled and its
   exact former name is preserved for possible recovery. Verify the native
   alias still has unchanged routing, defaults and audit dates.
3. Install the team consumer. Run its ORM suite and the browser suite above;
   compare the CRM snapshot and check the same website and alias invariants again.

## Outstanding release gates

- Independent checker reproduction and access-owner approval; no self-approval.
  Ask the checker to reproduce STPC01–02, 04–05 and 08–11 on a staging copy,
  including switching selected companies in the report and inspecting native
  salesperson permissions. Verify the report lists only records the tester can
  access; an empty view is not global clearance.
- Category base issues identified during review remain prerequisite risks:
  hard references to removable native stages in the starter hook, broad
  label-based menu deletion, and “All Opportunities” still using native
  assigned-to-me defaults. They are not silently changed in this consumer.
- Before enabling the consumer: PR #7 approved merge through `20`, then retire
  legacy intake and smoke-test the actual merged staging build. Verify disabled
  custom routes, unchanged native routes, and review existing incompatibilities
  in each intended company before explicitly mapping or reclassifying records.
- Replacement website/email intake and explicit recovery stay in issue #6; they
  are not a team-foundation rollout prerequisite.
- Generic dropdown/stage-rule consumers are not available/co-installed; their
  eventual intersection and Save/Discard integration remain a separate gate.
- Actual inbound mailbox, Odoo.sh/client staging/UAT, selected-company browser
  rehearsal and production-sized profiling are not implied by local tests.
- Agree a performance dataset/budget before calling any measurement a benchmark.
- Confirm a restorable, matching database/filestore/code backup and rehearse
  restore before rollout. If routing or access checks fail, stop adoption and
  use a reviewed forward fix or restore the matching set. Uninstall/checkout
  alone is not a database rollback strategy.

No push, new PR, integration-branch merge, deployment or issue closure was
performed during local preparation. The [PR draft](pull-request-draft.md) is
ready for review handoff.
