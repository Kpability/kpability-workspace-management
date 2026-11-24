# Pipeline categories: implementation and verification

| Item | Recorded baseline |
| --- | --- |
| Branch / add-on | `fix/defer-pipeline-website-email` / `kpability_pipeline_categories` |
| Version / license | `20.0.1.2.0` / LGPL-3 |
| Owner / checker | Fyke / independent checker to confirm with Sir Roy |
| Source delivery target | November 13, 2026 (S1 p.1), not a release approval |
| Status | Core CRM retained; website/email intake deferred November 13, 2026 |
| Publication | Follow-up to merged PR [#4](https://github.com/Kpability/kpability-workspace-management/pull/4), based on `20`; deferred work tracked in [issue #6](https://github.com/Kpability/kpability-workspace-management/issues/6) |

This replaces the earlier proposal. Read [shared standards](../../docs/development/shared-standards.md)
for S1–S4/U1, ownership, security, evidence and release requirements, and the
[add-on guide](../README.md) for configuration.

## 1. Requirements and approved scope

| Requirement | Source | Implementation |
| --- | --- | --- |
| PC-R1: pipeline categories | S1 p.1; S4 p.1 | Record-backed configuration, CRM classification and scoped pipelines |
| PC-R2: team/category integration contract | S4 p.1 | Stable base model/field; team mapping remains a separate consumer |
| PC-R3: reusable lookups | S1 p.2; S2 pp.1–3 | No client-specific lists or Studio; standalone install and second-dataset tests |
| PC-R4: maintainable naming/modules | S1 pp.1–2 | Root-level add-on, prefixed custom text/numeric fields, native inheritance |
| PC-R5: visible proof | U1; S3 pp.3–4 | Case-linked browser screenshots/recordings; independent review still required |

The user confirmed the following implementation decisions; these details are not
attributed to the PDFs:

- A **separate add-on**, independent of `workspace_management`.
- Pipeline-specific documentation, tests and ignore rules live inside the add-on;
  shared project standards and reference PDFs remain at repository level.
- **One optional category** per lead/opportunity; no silent backfill or mandatory
  selection. Existing unclassified records retain native CRM behavior.
- **Reusable stages** through a many-to-many mapping, with native **global stage
  order**, not category-specific ordering. **Reorder Stages** uses the native
  `sequence` handle, scoped to the stages mapped to that category.
- Both **shared** categories (`company_id=False`) and **company-specific** ones.
- A Helpdesk-style **Sales → Pipelines** overview with one clickable card per
  category, without an Open badge/button. Clicking a card provides a hard
  record filter, mapped stage columns and quick-create default. **All
  Opportunities** and **Uncategorized** remain reachable for native/legacy data.
- A minimal shared **General Sales** starter category mapped to native New,
  Qualified, Proposition and Won. Installation does not backfill records.
- Category configuration lives under **CRM → Configuration → Pipeline →
  Pipeline Categories** for Sales Managers. Sales users get read-only category
  access and the operational overview.
- Simplified category stage UI hides Sales Teams, Is Won and Folded; those native
  fields and semantics are retained on the native stage views/actions.
- Website forms and incoming-email integrations from PR #4 are **deferred**.
  Only a non-functional compatibility layer remains for safe upgrades; neither
  feature is offered in the current CRM-only delivery.
- Local **Odoo 20 Enterprise** development/testing, then authorized Odoo.sh
  integration/UAT. No deployment is implied by local implementation.

Team/category mapping, stage rules, dependent dropdown engines, territory,
reasons, activity templates, company RBAC and global Save/Discard remain out of
scope. PR [#1](https://github.com/Kpability/kpability-workspace-management/pull/1)
provides the native-inheritance baseline; existing User Roles code is unchanged.
PR [#2](https://github.com/Kpability/kpability-workspace-management/pull/2) was
open/conflicting when inspected and is not a dependency or merged component.

## 2. Actual Enterprise baseline

| Component | Tested value |
| --- | --- |
| Official Odoo server, sibling `../odoo` | `20.0`, commit `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e` |
| Official Enterprise, sibling `../enterprise` | `20.0`, commit `7773cfc038583d1b664491128424cd1904be946c` |
| Runtime edition | Session reports **`20.0+e`**; `web_enterprise` and `crm_enterprise` installed |
| Python / PostgreSQL | CPython **3.12.14** / PostgreSQL **16.15** |
| Browser | Playwright **1.65.0**, Chromium **158.0.8127.18** |
| Local database service | Dedicated `kpability-odoo20-db`, volume `kpability-odoo20-pgdata`, loopback port **55420** |
| Current local browser endpoint | `http://127.0.0.1:18027`, disposable database `kpability_pipeline_defer_fresh` |

This is an Enterprise development/trial database, not a claim of production
license activation. The Enterprise checkout alone is not an Odoo server; the
official server and its requirements were provisioned separately. Other local
applications/databases were not reused. Compatibility claims apply to the tested
pair above, not every Odoo 20 revision.

Native findings driving the implementation:

- `crm.tag` is generic classification, not a category/stage policy; no equivalent
  dedicated category model was found in the inspected CRM/Enterprise sources.
- Odoo 20 stages already have **`team_ids`**, with no native `company_id` or
  `active`. Category filtering intersects native team visibility/eligibility.
- Hooks use the actual `_stage_find(team_id=False, domain=None, order='sequence,
  id', limit=1)` and `_read_group_stage_ids(stages, domain)` APIs.
- Native bulk Won finds stages on the entire recordset. Categorized records are
  grouped by category/team before delegating to native Won; eligible Won stages
  are checked before any batch mutation.
- Security uses Odoo 20's **`ir.access.csv`** operation/domain format and native
  sales groups, not a copied legacy ACL schema or a new role system.

## 3. Data, security and lifecycle contract

| Object / field | Contract |
| --- | --- |
| `crm.pipeline.category` | `_rec_name='s_name'`; ordered by `n_sequence,s_name,id` |
| `s_name`, `s_description`, `n_sequence`, `active` | Translatable label/description, category ordering and archive state |
| `company_id` | Empty means shared; otherwise record company must match |
| `stage_ids` | Authoritative editable mapping to existing native stages |
| `s_normalized_name` | Stored canonical-name uniqueness helper; precomputed on insert |
| `lead_count` | Active-opportunity count in the configuration list; respects lead ACL/company rules |
| `crm.pipeline.category.alias` | Read-only historical configuration, retained solely for safe upgrades; no category `alias_ids` field/UI |
| `s_deferred_alias_name` | Exact previous native alias name retained when the owned alias is disabled |
| `crm.lead.pipeline_category_id` | Optional, indexed, tracked, `check_company=True`, restricted deletion; displayed as **Category** |
| `crm.lead.pipeline_category_stage_ids` | Related stage set used by native field domains |
| `crm.stage.pipeline_category_ids` | Read-only inverse using the same relation table |

Mappings are edited **only on categories**, including through RPC. This avoids a
stage form replacing mappings belonging to companies the editor cannot see.
Native stage duplication remains available without copying category mappings.
**Reorder Stages** opens only the mapped stages in the native `crm.stage`
sequence-handle list; it does not expose Sales Teams, Is Won or Folded in the
category workspace.

The **Pipelines** overview is a Kanban of clickable categories without a separate
Open badge/button. The configuration list retains an opportunity count using a
regular `crm.lead` read-group, obeying the current user's record rules and company
access. Clicking a card runs `action_open_pipeline()`, which returns the
native CRM board action with a hard category domain and category-scoped stage
columns. Configuration remains in **CRM → Configuration → Pipeline → Pipeline
Categories**; the former Sales configuration duplicate is removed on upgrade.

The `20.0.1.2.0` migration retains historical alias rows and their original
configuration, records the exact native alias name, and clears only the owned
native aliases' `alias_name` so they no longer receive new messages. It is
idempotent and leaves unrelated native aliases alone. The custom
`mail.thread.message_route` and `crm.lead.message_new` overrides are removed.
Normal native email processing and reply threading remain available.

The retired website module retains existing `website_ids` mappings and XML IDs,
but no Websites tab, editor block, category-list endpoint or fan-out behavior.
Old template references render a non-interactive notice; copied forms are
disabled and stale pipeline-specific POSTs are rejected. Native website forms
are not disabled. A hidden empty notebook remains only as an inheritance anchor
while older installed website companions complete their upgrade.

Sales users read permitted categories; Sales Managers configure them. A global
company rule allows shared categories and selected allowed companies. Shared
configuration has cross-company effect but grants **no opportunity access**.
Companyless opportunities may use shared categories only.

Names use NFKC, collapsed whitespace and case-folding on the canonical label.
`UNIQUE NULLS NOT DISTINCT(company_id,s_normalized_name)` also enforces uniqueness
in the shared scope. Archived names remain reserved; other company/shared scopes
may reuse the same label.

ORM checks, not just UI domains, reject incompatible category/stage/team/company
combinations. Category changes preserve the current stage until the user chooses
a compatible replacement or clears the category. No onchange auto-save/reset is
introduced. Native team-change behavior and Won/Lost buttons remain native.

An empty mapping does **not** mean all stages. New classified records need an
eligible mapped stage; Open Pipeline reports an empty configuration. A categorized
Won action requires an eligible mapped Won stage. Merge requires matching
classification, including classified versus unclassified records.

Archiving preserves historical references and unrelated edits but blocks new
assignments. Used categories cannot be deleted. Mapping/company/team changes
that invalidate existing records, including archived or inaccessible ones, are
blocked until explicit reclassification. Narrow `sudo()` existence-only checks
protect integrity without disclosing hidden IDs, names or counts. Category
configuration retains native create/write audit metadata; no custom audit engine
or category chatter was added.

## 4. Layout and consumer contract

```text
kpability_pipeline_categories/
  .gitignore
  __init__.py, __manifest__.py
  docs/pipeline-categories.md
  docs/evidence/
  models/crm_pipeline_category.py, crm_pipeline_category_alias.py,
          crm_stage.py, crm_lead.py
  migrations/20.0.1.2.0/post-migrate.py
  security/ir.access.csv
  views/crm_pipeline_category_views.xml, crm_stage_views.xml, crm_lead_views.xml
  tests/test_pipeline_categories.py
  tests/e2e/test_pipeline_categories.py
  README.md
kpability_website_pipeline_categories/
  __manifest__.py
  controllers/main.py
  models/crm_pipeline_category.py
  static/src/js/pipeline_category_form.js
  views/crm_pipeline_category_views.xml, website_templates.xml, snippets.xml
  tests/test_website_pipeline_categories.py
  README.md
```

The browser runner is not imported by `tests/__init__.py`; normal Odoo test
loading does not require Playwright.

The base add-on depends only on `crm` and ships no custom frontend assets. The
retired website module retains only a small copied-form deactivation guard.
Native form, quick-create, list, search, Kanban and stage views are
inherited, preserving Enterprise view types and native actions rather than copying
them.

The team consumer can depend on this add-on and use the model/fields above and
`category._check_assignable()` (read-access and active-category checks). Further
eligibility must narrow, never broaden, native/category policy. The base add-on
does not depend on that consumer or the later generic dropdown module.

## 5. Reproducing local checks

Commands below test the compatibility layer as well as the core; new deployments
should install only the core module. Run from this repository root. Use the recorded sibling checkouts
and a disposable PostgreSQL 16+ database. Supply `ODOO_DB_PASSWORD` separately;
do not commit local credentials. Stop a server before updating **its** database.

```bash
/tmp/opencode/kpability-odoo20-venv/bin/python ../odoo/odoo-bin \
  --addons-path="../enterprise,../odoo/addons,$PWD" \
  --db_host=127.0.0.1 --db_port=55420 --db_user=odoo \
  --db_password="$ODOO_DB_PASSWORD" --database=kpability_pipeline_verify \
  --init=kpability_website_pipeline_categories,crm_enterprise,web_enterprise \
  --without-demo=True --test-enable \
  --test-tags=/kpability_pipeline_categories,/kpability_website_pipeline_categories \
  --stop-after-init --http-interface=127.0.0.1 --http-port=18024 \
  --data-dir=/tmp/opencode/kpability-odoo20-data
```

For a subsequent module-update check, replace `--init=...` with
`--update=kpability_pipeline_categories,kpability_website_pipeline_categories` on
that same disposable database.
The Odoo virtual environment uses Python 3.12, `../odoo/requirements.txt`,
`websocket-client==1.9.2` and `markdown2==2.5.5`.

The browser runner uses a **separate** Python environment containing
`playwright==1.65.0` and its installed Chromium (`python -m playwright install
chromium`). Start the installed test database on loopback port 18027, then:

```bash
ODOO_E2E_ALLOW_WRITES=1 \
ODOO_E2E_URL=http://127.0.0.1:18027 \
ODOO_E2E_DATABASE=kpability_pipeline_defer_fresh \
ODOO_E2E_LOGIN=admin ODOO_E2E_PASSWORD="$ODOO_BROWSER_PASSWORD" \
  uv run --no-project --with playwright==1.65.0 python \
    kpability_pipeline_categories/tests/e2e/test_pipeline_categories.py
```

It requires the explicit write opt-in and refuses non-localhost URLs and
non-`kpability_pipeline_*` databases. It verifies Enterprise modules/version and creates synthetic
categories, stages, opportunities and a sales user. It intentionally retains the
dataset for inspection; never use client data. Screenshots, named videos and
`dataset.json` go under `/tmp/opencode/kpability-pipeline-e2e/<run_id>/` (override
the base directory with `ODOO_E2E_ARTIFACTS`). Do not run concurrent suites on the
same database.
When the retired website module is installed, the browser suite also checks that
a synthetic legacy copied form is disabled and the old category endpoint is gone.

## 6. Historical results, November 12, 2026 (before deferral)

The following results describe PR #4, **not** the current CRM-only release.
PC-13/PC-14 and their website screenshots are historical and deferred under
issue #6. Current cleanup verification is recorded separately below.

| Check | Actual result / evidence |
| --- | --- |
| Fresh Enterprise install of both add-ons | **52 passed** (50 feature tests + 2 native web post-tests), zero failures/errors; `/tmp/opencode/kpability-pipeline-leader-followup-fresh.log` |
| Module update on the installed test database | **50 passed**, zero failures/errors; `/tmp/opencode/kpability-pipeline-leader-followup-tests-final.log` |
| Existing native data, initial add-on install | Earlier run: three open/Won/Lost opportunities retained exact name, active, stage, team, company, probability and revenue; all remained unclassified |
| Same-version module update | Earlier run: the three legacy records, one categorized record and its stage mappings retained exact snapshots; Enterprise installed without `workspace_management` |
| Browser | **11 passed**; configuration/placeholder, overview without Open badge, scoped board/reload, simplified stage reorder, explicit Save/Discard, invalid save/RPC, sales-user read-only access, quick-create, invalid mouse drag, group-by, and public website selection creating two opportunities |

The latest browser run used `kpability_pipeline_final_test` on loopback port
18021 (run `1112075041`, **16.613s**); artifacts are in
`/tmp/opencode/kpability-pipeline-e2e/1112075041/`. The fresh install used the
separate disposable database `kpability_pipeline_followup_fresh` on port 18022.
Earlier runs `1112040040` and `1112040448` passed the original ten browser cases;
their evidence is historical. The suite verifies persisted values through actual
RPC as well as the visible interface and fails on unexpected JavaScript page
errors.

Lifecycle logs from the earlier native-data checks remain
`/tmp/opencode/kpability-pipeline-upgrade-install.log` and
`/tmp/opencode/kpability-pipeline-upgrade-update.log`. That is installation over
native data and a same-version module update, **not** a cross-major migration. The
latest fresh-install and update runs above use disposable databases.

| Case | Executed coverage | Remaining acceptance evidence / gate |
| --- | --- | --- |
| PC-01 | ORM CRUD/order/inverse/ACL; manager form and sales-user browser access | Checker reproduction of interactive create/reorder |
| PC-02 | Canonical/shared/company uniqueness, whitespace and blank-label ORM tests | Visible duplicate-error capture |
| PC-03 | Initial stage/team eligibility; scoped exact columns and reload; mapped form statusbar | Checker review |
| PC-04 | Invalid create/write/spoofed context; visible invalid save and mouse drag; actual RPC rejection | Import-wizard rehearsal (ORM path covered) |
| PC-05 | Search/group counts; native browser group-by; scoped/form reload persistence | Checker interactive search/filter rehearsal |
| PC-06 | Archived history/unrelated edits/new assignment/delete/name reservation ORM tests | Archive/history browser capture |
| PC-07 | Multi-company/foreign/companyless/hidden-record ORM tests; real sales-user UI and denied RPC | Company-switch browser recording; access-owner review |
| PC-08 | Form and browser dirty edits, discard, valid save, explicit category/stage replacement and reopen | Checker reproduction |
| PC-09 | Standalone fresh Enterprise install; native lead conversion/duplication and unclassified behavior | Leads disabled/enabled settings UI rehearsal |
| PC-10 | Legacy install/update snapshots; hidden/archived mapping and scope-edit rejection | Checker configuration-removal UI check |
| PC-11 | Second company/dataset reuse test, without code edits | Optional team-consumer co-installation and reuse recording |
| PC-12 | Starter/defaults/list counts/ACL; browser overview has no Open badge and card opens the scoped board | Checker reproduction on client data |
| PC-13 | Alias CRUD/ACL plus native incoming-mail processing: three addresses produce two pipelines, correct company/stages, attachments, repeat delivery suppression and reply threading | Real inbound gateway rehearsal on staging |
| PC-14 | Availability/endpoint, duplicate selection, unavailable-category rollback, attachment contents in both records; public browser form selects two pipelines, redirects successfully and persists both records | Website UAT on designated staging site |
| PC-15 | Browser Reorder Stages opens one business-facing list; no Sales Teams, Is Won or Folded columns | Checker reproduction with a reused native stage |

Additional ORM coverage includes native Lost/restore/rainbowman, per-category/team
bulk Won, missing Won preflight, merge conflicts/preservation, a 50-record batch
fixture, native incoming email processing and website category creation. The
batch fixture is **not** a production performance benchmark.
Native stages have no archive flag, so no invented stage-archive case is claimed.
Curated [visual evidence](evidence/README.md) is retained in
the repository; full raw artifacts remain local. All PC cases are **not** marked
release-complete: the remaining column and independent review still apply.

## 7. Current deferral verification, November 13, 2026

The cleanup is based on merged PR #4 (`cf54708dd35761c9a3e09d27a0bb2aa711f4b378`).
It removes the custom website/email delivery while keeping core CRM behavior.
The retired companion remains only because existing installations must be able
to upgrade without dropping their configuration. Issue #6 stays open for the
future separately reviewed integrations.

| Check | Actual result |
| --- | --- |
| Fresh core-only Enterprise install | **47 passed**: 45 feature tests plus 2 native web tests; no failures/errors or warnings; `kpability_pipeline_defer_core`, `/tmp/opencode/kpability-defer-core-fresh.log` |
| Combined core/retired-companion regression | **53 passed**: 45 core and 8 compatibility tests; no failures/errors; `/tmp/opencode/kpability-defer-tests.log` |
| First upgrade from PR #4's installed versions | **53 passed**, no failures/errors or warnings; migration actually executed; `kpability_pipeline_defer_upgrade_final`, `/tmp/opencode/kpability-defer-upgrade-final.log` |
| Browser | **12 passed** in **17.975s**, run `1113013907`; existing ten CRM cases plus no intake tabs and a disabled copied website form |
| Static checks | Ruff E9/F, Python/XML parsing, relative documentation links and whitespace checks passed |

The upgrade fixture started with base `20.0.1.1.0` and website `20.0.1.0.0`,
then updated to `20.0.1.2.0` and `20.0.1.1.0`. Before/after snapshots verified:

- Both classified opportunities, including an archived Lost record, retained
  their name, category, stage, company, team, probability, revenue and audit date.
- All 2 categories, 4 stages, 6 website pages and their stored mappings/configuration
  were retained without changes; the legacy email configuration row was retained.
- All 4 native aliases were retained. Only the one owned pipeline alias was
  disabled; unrelated aliases and defaults stayed unchanged.
- The exact native alias name was archived even when it differed from the
  historical wrapper name. Re-running retirement caused no further writes.
- The old editor snippet and category inheritance view became inactive; the old
  template XML ID still resolves but no longer contains a form.

The alias's computed display label intentionally becomes **Inactive Alias**;
its stored relation ID is unchanged. The compatibility tests additionally verify
that stale checkbox/list submissions create no opportunities or attachments,
the public category endpoint returns 404, and ordinary native email/replies and
website CRM forms continue to work.

Current [two-screenshot evidence](evidence/intake-deferral-2026-11-13/README.md)
shows the category form without intake tabs and the working scoped pipeline.
Raw browser artifacts remain in `/tmp/opencode/kpability-pipeline-e2e/1113013907/`.
These checks used isolated local Enterprise databases, not the Odoo.sh database.
They are not a production rollback exercise, external email-delivery certification
or independent checker approval. Earlier PC-13/PC-14 success evidence is historical,
not a feature offered by this cleanup.

## 8. Integration, rollout and outstanding gates

1. Confirm checker/access-owner review and reproduce the outstanding case evidence
   above; attach case-linked screenshots or recording when a PR is authorized.
2. Co-install the team consumer, stage rules and PR #2 reasons only when available
   on a compatible branch. Preserve their native hooks; no wholesale PR #2 copy
   or conflict resolution was attempted here.
3. Agree production-scale data/performance thresholds and profile accordingly.
4. When authorized, test the exact published commit on the designated Odoo.sh
    development/staging branch. Publishing the feature PR does not approve a merge
    or client deployment; Odoo.sh validation remains unverified.
5. Inventory client-native/custom stage usage before rollout. Do not infer or
   automatically backfill categories; obtain approval for explicit mappings.
6. Back up the matching database, filestore and code pair before release. Use a
   tested matching restore for rollback, not a code-only checkout after schema
    changes. Production approval is separate from this local implementation.

Historical note from the November 12 review: the supplied
[development CRM URL](https://kpability-kpability-workspace-management-feature-pi-41756670.dev.odoo.com/odoo/action-272)
redirected to login. The public `/kpability/pipeline-categories` endpoint returned
`[]`. No remote form submission, configuration change or email was attempted;
staging testing needs an authorized test account, website-enabled categories and
a usable incoming email address/gateway. Local native-mail tests do not validate
external mail delivery.
