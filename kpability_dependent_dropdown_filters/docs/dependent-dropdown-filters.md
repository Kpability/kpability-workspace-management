# Dependent dropdown filters — implementation record

**Local implementation:** November 15, 2026. **Release status:** not certified
or deployed. Maker: Fyke; independent checker and HR/access owner still to confirm.

## Sources and decisions

The four PDFs reviewed are in the original company's workspace under
`docs/references/`. They are not copied into this isolated feature worktree.
Source IDs follow [shared standards](../../docs/development/shared-standards.md).

| Source | Requirement | Implementation / boundary |
| --- | --- | --- |
| S1, `Standard Implementation Considerations with Timelinepdf.pdf`, pp.1–2 | No Studio; descriptive names; maintained lookups; individuals under company; November 17 target | Installable inherited add-ons; `dropdown.filters` and `dropdown.adapter`; `s_*` text and `j_*` JSON; record-selected bindings. The source date is not a new completion promise. |
| S3, `Odoo Standardization - Fyke Focus.pdf`, p.2 | Sales-department salesperson and company individuals; CRM/Contacts reuse; configuration rather than per-client code | Two company/contact bindings and two optional department bindings. Administrators maintain company/department configuration without code; adding a new supported field/view still requires a reviewed adapter. |
| S3 pp.2–4; S4, `Odoo Standardization.pdf`, p.2 | UI filters are not security; company access; understandable Save/Discard; visible test evidence | Native ACLs/company rules plus approved create/write invariants; preserved stale values; native Save/Discard; guarded browser evidence. |
| S1 p.2; S4 p.2 | Playwright; shared Save/Discard and other owners' work | Local Playwright checks now; alignment with TJ's November 25 harness later. No dependency on or replacement for Thirdy's buttons/RBAC, stage rules or territory modules. |
| S2, `Odoo Submodules.pdf`, pp.1–4, 10–11 | Reusable modules, separate tested feature work, independent client adoption and staging before production | Generic core has no CRM/HR dependency; optional adapters; isolated branch. Publishing, submodule pinning, staging and deployment require separate approval. |

The user explicitly approved the two new relational fields, direct active
individuals only, empty parent → no choices, retaining stale values with explicit
repair, native-domain intersection, disabled creation shortcuts, and an exact
department reference per tenant using active internal users/active employees
without new private-HR permissions. These implementation decisions do not replace
checker, HR-owner or deployment approval.

The workflow and repository conventions were compared with
[PR #4](https://github.com/Kpability/kpability-workspace-management/pull/4),
`feature/pipeline-categories`, and the existing sales-team implementation:
module-local code/docs/tests, native inherited views, Odoo 20 permissions,
explicit configuration, changed-relationship validation, legacy preservation and
synthetic visual evidence. No sibling code was modified. The approved default
branch `origin/20` was subsequently merged as described below; unreviewed sibling
branches and the original dirty sales-team worktree were not included.

## Exact baseline and native gap

| Component | Verified baseline |
| --- | --- |
| Community source | `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e` |
| Enterprise source | `7773cfc038583d1b664491128424cd1904be946c` |
| Full local runtime | `20.0+e`, including `web_enterprise`, `crm_enterprise`, `contacts`, `hr` |
| Python / PostgreSQL | CPython 3.12.14 / isolated PostgreSQL 16 container |
| Add-on versions | All three `20.0.1.0.0`, LGPL-3 |
| Feature baseline | Existing `feature/dependent-dropdown-filters`, originally `fa14da4`; implementation commit `bd41e2f`; default `origin/20` at `cf54708` merged without conflicts in `0429dac` |
| Post-merge tested source | `9bb479d`; three optional integration checks added, with no runtime implementation changes |

Native CRM `partner_name` is text and `company_id` identifies the tenant, not a
customer company. Native `user_id` limits internal users but not department
membership. The approved additions are CRM `customer_company_id` and company
Contacts `primary_contact_id`; native fields retain their names and semantics.

Inspected native APIs: `odoo.fields.Domain`, `models.Constraint`, Odoo 20
`ir.access` CSV permissions, CRM's separate lead/opportunity Contact selectors,
Contacts' Sales & Purchase fields, and `hr.employee.public` access. Native
`Many2OneField` already supports a computed domain and server-side pagination.
No replacement widget or global search patch is needed.

On this exact build, `res.partner.is_company` is computed from commercial-partner
classification and VAT. Synthetic fixtures use that native behavior; this module
does not force company classification. Native CRM salesperson/team/company
recomputations likewise remain unchanged.

## Delivered surface

| Binding | Form / target | Parent / context |
| --- | --- | --- |
| CRM customer contact | `crm.crm_lead_view_form`, both native `partner_id` instances | `customer_company_id` |
| Contacts primary contact | `base.view_partner_form`, Sales & Purchase, `primary_contact_id` | Persisted company record itself |
| CRM salesperson, optional HR | Native CRM `user_id` widget and team context | Record tenant company and maintained department |
| Contacts salesperson, optional HR | Native Sales & Purchase `user_id` widget | Record tenant company and maintained department |

Core: `kpability_dependent_dropdown_filters`, depending only on `base`, `web`.
CRM/Contacts: `kpability_dependent_dropdown_crm_contacts`, adding `crm`, `contacts`.
Optional HR: `kpability_dependent_dropdown_hr`, adding `hr`.

Only code-registered binding catalog records are installed. There are **no seeded
filter rules, department mappings, automatic assignments or data backfills**.
New filters default inactive. Settings administrators maintain them through the
native configuration form; internal users have company-scoped read access for
runtime resolution. The supported-binding catalog is read-only to normal users.
One configuration exists per tenant/binding, including inactive records.

The resolver combines installed Python/check-company domains and the reviewed
view predicates with the configured restriction using AND. Literal Python field
domains are parsed as literals, never executed; unsupported future expression
domains fail explicitly instead of broadening results. Configuration has no
executable expressions. No `sudo`, `any!`, raw SQL, shared cache, unrestricted
metadata selection or global `name_search` override is used.

Company/contact bindings accept active non-company **direct** children only.
An unsaved, missing, inaccessible or ineligible parent cannot open an unrestricted
picker. Existing readable stale values remain, accompanied by a warning.
Create/write checks new or changed final relationships after native computation,
including normal RPC/import paths; a caller-supplied context flag cannot bypass
them. Unchanged legacy relationships permit unrelated edits. Explicit clearing
or an atomic valid parent/child change is supported.

The HR predicate uses the normal-access `employee_public_ids any` relation,
restricted to active employees in the record's tenant and exact configured
department. Users must be active, internal and natively company-eligible.
Department names and descendants are not matching criteria. Ordinary sales
users were verified against the native public projection, with private HR-field
reads and configuration writes denied; no private-HR permissions were added.

## Local verification

All database operations were against newly created `kpability_ddf_*` databases
in the owned `kpability-ddf-postgres` container, bound to
`127.0.0.1:55427`. No company database was connected to. The original dirty
sales-team worktree was left untouched.

| Check | Actual result / evidence |
| --- | --- |
| Core-only fresh install, without CRM/HR | 7 authored tests pass (9 including framework tests); `/tmp/opencode/kpability-ddf-core.log` |
| CRM/Contacts without HR | 19 authored tests pass; `/tmp/opencode/kpability-ddf-contacts-2.log` |
| Earlier full Enterprise regression | Before integration, 27 authored checks passed on fresh install and upgrade; `/tmp/opencode/kpability-ddf-enterprise.log`, `/tmp/opencode/kpability-ddf-final-tests-2.log` |
| Post-merge combined fresh Enterprise install | 82 pass: 30 dropdown + 43 approved pipeline-category + 7 website + 2 framework checks; zero failures/errors; `/tmp/opencode/kpability-ddf-postmerge-fresh-final.log` |
| Post-merge combined upgrade regression | 80 authored checks pass, zero failures/errors; `/tmp/opencode/kpability-ddf-postmerge-upgrade-final.log` |
| Existing-record installation and same-version upgrade | Exact assignment/audit-field snapshots pass, including another post-merge upgrade; `/tmp/opencode/kpability-ddf-lifecycle.json`, `/tmp/opencode/kpability-ddf-postmerge-lifecycle-check.log` |
| Post-merge actual Brave remote-debugging evidence | 10 cases pass at `/tmp/opencode/kpability-ddf-browser/20261115152849/`, engine `156.0.8078.80`, CDP transport and Brave identity recorded, no page JavaScript/console errors; [committed screenshots and results](evidence/README.md) |
| Earlier bundled Chromium evidence | 5 cases pass on `158.0.8127.18`; historical evidence, not claimed as Brave testing |
| Native-view/static checks | Native view validation and `git diff --check`; UI detector returned no findings before final access-group alignment |

Final model-test log warnings are native missing optional `markdown2` rendering
support; no remaining custom-view access inconsistency was reported. Earlier
failing iterations are retained locally and are not passing evidence.
The integration added three tests for valid contact repair/category preservation,
unchanged legacy contacts during category changes, and department validation
alongside categorized Won/lost behavior. The first integration iteration expected
Won → lost directly; native Odoo correctly rejects that transition. The corrected
test asserts the guard and moves to an eligible stage before losing. No native
workflow was changed to make tests pass.

The additional verification changed tests and documentation, not runtime
application code. It used the user's approved remote-debugging connection
and new owned browser contexts against the same synthetic database. Existing
tabs and browser settings were not inspected or changed.

### Reproduction commands

These commands describe the local disposable environment, not a company rollout.
Do not point them at a company database. Set paths to the verified source trees
and current feature worktree:

```bash
PY=/tmp/opencode/kpability-ddf-venv/bin/python
ODOO=/home/arnecronomica/Utilities/Projects/odoo/odoo-bin
ADDONS=/home/arnecronomica/Utilities/Projects/enterprise,/home/arnecronomica/Utilities/Projects/odoo/addons,/tmp/opencode/kpability-dependent-dropdown-filters
MODULES=kpability_dependent_dropdown_filters,kpability_dependent_dropdown_crm_contacts,kpability_dependent_dropdown_hr
TAGS=/kpability_dependent_dropdown_filters,/kpability_dependent_dropdown_crm_contacts,/kpability_dependent_dropdown_hr
```

Post-merge combined upgrade regression, including only the approved default
branch's pipeline/website modules:

```bash
COMBINED_MODULES="$MODULES,kpability_pipeline_categories,kpability_website_pipeline_categories"
COMBINED_TAGS="$TAGS,/kpability_pipeline_categories,/kpability_website_pipeline_categories"
"$PY" "$ODOO" --addons-path="$ADDONS" \
  --db_host=127.0.0.1 --db_port=55427 --db_user=odoo \
  --database=kpability_ddf_enterprise \
  --data-dir=/tmp/opencode/kpability-ddf-enterprise-data \
  --http-interface=127.0.0.1 --http-port=18043 \
  --update="$COMBINED_MODULES" --without-demo=all \
  --test-enable --test-tags="$COMBINED_TAGS" --stop-after-init \
  --logfile=/tmp/opencode/kpability-ddf-postmerge-upgrade-final.log
```

For the new combined fresh installation, use
`--init=web_enterprise,crm_enterprise,workspace_management,kpability_dependent_dropdown_hr,kpability_website_pipeline_categories`
instead of `--update`, the same combined tags, `--without-demo=all`, a **new**
`kpability_ddf_*` database and its own data directory/HTTP port. The passing run
used `kpability_ddf_combined_final`, data directory
`/tmp/opencode/kpability-ddf-combined-final-data`, port `18047`, and log
`/tmp/opencode/kpability-ddf-postmerge-fresh-final.log`. Core-only installs initialize
just the core module; CRM/Contacts initializes that adapter without HR.
Do not share a running test server/database with an install/upgrade process.

Lifecycle script: native Enterprise CRM/Contacts/HR was installed first without
these add-ons; then `tests/check_lifecycle.py` ran through `odoo-bin shell`
with `DDF_ALLOW_WRITES=1` and `DDF_LIFECYCLE_PHASE=before`, followed by installing
the HR adapter and running `after_install`, updating all three and running
`after_upgrade`. It is hard-guarded to `kpability_ddf_legacy` on the local fixture
port, refuses to overwrite the initial snapshot, and checks zero installed
filter rules, blank new business fields and exact preserved values/audit dates.

Browser preparation: run `tests/e2e/prepare_local_fixture.py` through
`odoo-bin shell` on the owned full fixture with `DDF_ALLOW_WRITES=1`. It refuses an
existing fixture or existing rules and creates only synthetic records and
test-only active configurations. Random credentials are stored outside Git with
mode `0600`. Start the full local server with
`--http-interface=127.0.0.1 --http-port=18043 --db-filter='^kpability_ddf_enterprise$'`.
Then, from the worktree root:

```bash
DDF_ALLOW_WRITES=1 uv run --no-project --with playwright==1.65.0 \
  python kpability_dependent_dropdown_filters/tests/e2e/test_dependent_dropdowns.py
```

That command launches bundled Chromium unless `DDF_CDP_URL` is supplied. For
actual Brave, obtain the browser WebSocket endpoint from the explicitly approved
local remote-debugging session, then run:

```bash
: "${APPROVED_LOCAL_CDP_WEBSOCKET:?Set the approved localhost Brave browser WebSocket endpoint}"
DDF_ALLOW_WRITES=1 DDF_CDP_URL="$APPROVED_LOCAL_CDP_WEBSOCKET" \
  uv run --no-project --with playwright==1.65.0 \
  python kpability_dependent_dropdown_filters/tests/e2e/test_dependent_dropdowns.py
```

The runner rejects non-local/browser CDP endpoints and allows time for the human
connection-consent prompt. Do not bypass that prompt or publish the endpoint.
The actual run attached to Brave on `127.0.0.1:9222` and recorded
`navigator.brave.isBrave() == true`. It closes only its own contexts and
disconnects; it does not close the attached browser. The native application's
effective desktop viewport was calibrated without changing the user's site zoom.

Run Playwright separately from Odoo's environment to preserve Odoo's pinned
`greenlet==3.0.3`. Synthetic credentials and raw videos/logs remain outside Git.
Curated synthetic screenshots and a non-secret results manifest are published
under the user's explicit feature-PR authorization. The runner requires explicit
opt-in, localhost and a synthetic
database name; fixture/lifecycle writers also check the dedicated database port.

## Acceptance coverage and remaining gates

| Cases | Covered locally | Still required |
| --- | --- | --- |
| DDF-01 | Config round-trip, invalid binding/duplicate rejection, privileged writes, company-scoped read; native UI department change applies without code after reopening | Checker reproduces configuration UI and access policy |
| DDF-02–03 | CRM lead/opportunity selectors, autocomplete/Search More, Contacts reuse, second tenant config | Client-specific fields/views and combined extensions |
| DDF-04–06 | Missing/empty/unsaved/inaccessible parent, archive/grandchild exclusion, draft preservation, explicit repair, native Save/Discard; actual-Brave empty-result, keyboard and controlled older-onchange/latest-parent checks | Wider concurrency orderings and keyboard/mobile/accessibility coverage |
| DDF-07–08 | Exact department/public mapping, no employee, archived employee, department rename/change, no cached membership, company mapping and private-HR denial | HR-owner privacy approval, additional portal/inactive-user/multiple-company employee fixtures |
| DDF-09–10 | Native AND, company boundaries, backend create/write/RPC denial, no public bypass, unsupported catalog rejection, no creation shortcut on adapted forms | Import-tool UI, alternative widgets/views and external integration review |
| DDF-11 | Fresh install, same-version upgrade, exact synthetic legacy/audit preservation; deactivation/reactivation verified in the native selector and unchanged legacy edit | Uninstall/restore rehearsal and activation-time production mismatch report |
| DDF-12 | Core without CRM/HR; CRM/Contacts without HR; full Enterprise plus approved pipeline/website categories; category/Won/lost, contact repair, unchanged legacy and department coexistence checks | Integration with unmerged team/stage modules and shared Save/Discard |

The browser dataset contains two customer companies, 12 eligible direct contacts,
one other-company contact and an archived contact, with two departments and two
sales users. This is functional proof, **not** a production performance
benchmark. No production-sized dataset, agreed query/time budget or performance
certification is claimed.

Known compatibility boundaries:

- Only the four supported native form bindings are adapted. Alternative views,
  kanban quick creation, conversions and future domain/assignment extensions need
  explicit review; backend checks still apply to changed assignments.
- Creation shortcuts remain disabled while the adapted views are installed,
  even with configuration inactive. Deactivation restores native choice policy,
  not these shortcut attributes.
- Reopen forms after rule/membership changes. No live-push invalidation is
  implemented; changed assignments are always checked against current rules.
- Editing a contact's hierarchy, HR membership or configuration does not migrate
  historical documents. There is no automatic repair or cross-document rewrite.
- External/portal business integrations are not certified by these internal-user
  fixtures. Helper fields are internal-only; no new external configuration or
  HR read permissions are granted. Review external create/write routes before
  installing/activating in a client database.
- The branch was updated against the fetched default `origin/20` at `cf54708`
  without conflicts. Combined checks cover the approved category/website modules;
  unmerged team/stage/shared-button work still requires its own integration pass.

Independent maker/checker approval, approved HR access/legacy policy, Odoo.sh
staging/UAT, backup/restore and separately authorized deployment
remain mandatory. Do not treat a code rollback or uninstall as a tested database
downgrade. The user authorized this feature commit, push and PR, not a merge to
`20`, company activation, client adoption or deployment. Reference PDFs remain
outside the commit.
