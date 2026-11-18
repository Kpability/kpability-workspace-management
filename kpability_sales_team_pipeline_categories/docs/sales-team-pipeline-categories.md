# Sales Team Pipeline Categories — implementation record

## Scope and approved policies

Implementation began November 13, 2026 on the existing
`feature/sales-team-pipeline-categories` branch after incorporating approved
`origin/20` at `cf54708dd35761c9a3e09d27a0bb2aa711f4b378` (merged PR #4).
PR #7 remains open/review-required; the user explicitly chose **Foundation now**,
with website/email reintroduction pending its approved merge through `20`.

Approved policies replace the old proposal in `docs/development/`:

| Decision | Implemented policy |
| --- | --- |
| Cardinality | One authoritative `crm.team.pipeline_category_ids` M2M; read-only `crm.pipeline.category.sales_team_ids` inverse on `crm_team_pipeline_category_rel(team_id,category_id)` |
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
| Official Odoo Community source, `20.0` | `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`, sibling `../odoo`, official GitHub origin |
| Official Enterprise source, `20.0` | `7773cfc038583d1b664491128424cd1904be946c`, sibling `../enterprise`, official GitHub origin |
| Python | CPython 3.12.14; target source supports 3.12–3.14 |
| PostgreSQL | PostgreSQL 16.15, dedicated local container on loopback port 55420 |
| Edition | Runtime `20.0+e`, with `web_enterprise` and `crm_enterprise` installed; browser setup asserts both edition and modules |
| Add-on | `kpability_sales_team_pipeline_categories` version `20.0.1.0.0`, LGPL-3 |

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
  --db_host=127.0.0.1 --db_port=55420 --db_user=odoo \
  --db_password="$ODOO_DB_PASSWORD" --database=kpability_pipeline_stpc_fresh \
  --init=kpability_sales_team_pipeline_categories,web_enterprise,crm_enterprise \
  --without-demo=True --test-enable \
  --test-tags=/kpability_sales_team_pipeline_categories \
  --stop-after-init --http-interface=127.0.0.1 --http-port=18030 \
  --data-dir=/tmp/opencode/kpability-stpc-data
```

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
ODOO_E2E_URL=http://127.0.0.1:18030 \
ODOO_E2E_DATABASE=kpability_pipeline_stpc_fresh_final \
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

Executed locally on November 13, 2026, on the exact source/runtime baseline above:

| Run | Result | Local log / evidence |
| --- | --- | --- |
| Final-code fresh consumer + Enterprise install, `kpability_pipeline_stpc_verified` | **37 Odoo-reported checks; zero failures/errors**, including all 35 authored STPC methods | `/tmp/opencode/kpability-stpc-verified.log` |
| Final-code same-version consumer update, same disposable database | **35/35 authored STPC tests passed; zero failures/errors** | `/tmp/opencode/kpability-stpc-verified-update.log` |
| Existing category base alone + Enterprise, separate `kpability_pipeline_stpc_base` | **45 Odoo-reported checks; zero failures/errors**, including all 43 existing authored base methods | `/tmp/opencode/kpability-stpc-base.log` |
| Existing-record installation and same-version update | **Passed**: Open/Won/Lost/unclassified CRM, categories, stages and audit dates unchanged; no inferred mappings; explicit mapping retained on update | `/tmp/opencode/kpability-stpc-lifecycle.json`, `kpability-stpc-lifecycle-shell.log`, `kpability-stpc-existing-install.log`, `kpability-stpc-lifecycle-update.log` |
| Playwright 1.65.0 / Chromium 158.0.8127.18, runtime `20.0+e` | **7/7 passed**, no unexpected page JavaScript errors | `/tmp/opencode/kpability-stpc-browser/20261113024544/` |
| Python compilation / whitespace validation | Passed | `python -m compileall -q kpability_sales_team_pipeline_categories`; `git diff --check` |

The initial browser pass exposed test navigation assumptions and a modal onchange
warning during quick-create. Tests now use native Extra Info navigation, and the
warning is a non-blocking native notification that preserves the category.
The final fresh model run and all seven browser cases passed after that change.
Earlier failed diagnostic runs are not presented as successful verification.
Historical PR #4/#7 results are not counted as tests of this consumer.

| Cases | Authored coverage |
| --- | --- |
| STPC01 | M2M/inverse round-trip, authoritative-side enforcement including sudo/RPC, copy behavior |
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

## Outstanding release gates

- Independent checker reproduction and access-owner approval; no self-approval.
- Category base issues identified during review remain prerequisite risks:
  hard references to removable native stages in the starter hook, broad
  label-based menu deletion, and “All Opportunities” still using native
  assigned-to-me defaults. They are not silently changed in this consumer.
- PR #7 approved merge through `20`, retirement upgrade, and separately reviewed
  restored website/email intake, explicit recovery and issue #6 completion.
- Generic dropdown/stage-rule consumers are not available/co-installed; their
  eventual intersection and Save/Discard integration remain a separate gate.
- Actual inbound mailbox, Odoo.sh/client staging/UAT, selected-company browser
  rehearsal and production-sized profiling are not implied by local tests.
- Agree a performance dataset/budget before calling any measurement a benchmark.
- Backup/restore a matching database/filestore/code set before rollout. Installing
  the consumer does not migrate CRM rows; uninstall/checkout alone is not a
  database rollback strategy.

No push, new PR, integration-branch merge, deployment or issue closure is
authorized or performed by this implementation.
