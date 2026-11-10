# Development plan: Sales team pipeline categories

| Item | Plan |
| --- | --- |
| Branch | `feature/sales-team-pipeline-categories` |
| Target platform | Odoo 20; exact build and APIs unverified |
| Owner / checker | Fyke / checker to confirm with Sir Roy |
| Source delivery target | November 13, 2026 (S1 p.1) |
| Status | Proposed development plan only; no implementation or tests performed |
| Proposed add-on | `kpability_sales_team_pipeline_categories` |

Read [shared standards](shared-standards.md) for sources S1–S4/U1, PR evidence, ownership, security and release requirements. The prerequisite category plan lives on `feature/pipeline-categories` at `docs/development/pipeline-categories.md`; it is intentionally not duplicated here.

## 1. Objective and traceable requirements

Allow authorized editors to configure which pipeline categories apply to each sales team, with consistent CRM category/stage choices and reusable behavior across clients.

| Requirement | Source | Interpretation |
| --- | --- | --- |
| STPC-R1: sales team pipeline categories | S1 p.1 | Fyke delivers a separate module/branch, target November 13. |
| STPC-R2: flexible team/category association | S4 p.1 | Many-to-many was discussed: a team can use several categories and a category can serve several teams. Confirm final semantics before schema freeze. |
| STPC-R3: reusable maintained configuration, no Studio | S1 pp.1–2; S2 pp.1–3 | Record-backed mapping and no client-specific IDs or hard-coded lists. |
| STPC-R4: tested visual proof and checker review | U1; S3 pp.3–4 | Feature PR includes case-linked screenshots or recording. |

The sources do not define whether a team/category is mandatory, what no mappings means, category defaults, or whether mappings confer record visibility. Proposed defaults below require approval.

## 2. Scope, dependencies, and boundaries

### In scope

- Many-to-many team/category configuration, preferably editable from the sales team and readably accessible from category configuration.
- Team-dependent category options and resulting stage eligibility on CRM records, without broadening native team/stage restrictions.
- Safe behavior when a team or category changes, including dirty forms, quick-create, native assignment, imports/RPC and bulk edits.
- Configuration ACLs, company consistency, archive/removal policy and validation of existing records before mapping changes.
- Search/configuration views needed to inspect the mapping and demonstrate reuse.

### Dependencies

- Required: the approved pipeline-category module contract and native CRM. Candidate models to inspect are `crm.team`, `crm.lead`, and `crm.stage`.
- Base category module owns category CRUD, category/stage mapping, archive policy and record classification.
- This consumer owns team/category mapping, team narrowing and any explicitly approved invariant that a selected category belongs to the selected team.
- Do **not** depend on the generic dropdown module due November 17 to meet a November 13 target. Use a small supported CRM adapter; later reuse the dropdown engine only if it adds value without two competing filters.
- Stage rules may consume the resulting stage/category state but are not implemented here. Do not duplicate Thirdy's RBAC or TJ's territory/auto-assignment work.

### Out of scope

Team membership redesign, new salesperson assignment algorithms, territories, category-based record access, Won/Lost redesign, activity/templates/reasons, generic role management and global Save/Discard buttons.

## 3. Decision log to complete before implementation

| Decision | Proposed default | Approval / gate |
| --- | --- | --- |
| STPC-D1: relationship cardinality | One shared many-to-many relation; not separate unsynchronized mappings per view | Sir Roy/checker, November 10 |
| STPC-D2: empty team mapping | No categories offered for new categorized assignments; preserve native handling for unclassified legacy records. Do not silently interpret empty as unrestricted | Checker, November 10 |
| STPC-D3: missing team | Keep native unassigned records possible during migration; do not offer a categorized assignment until an eligible team is selected | Checker, November 10 |
| STPC-D4: default category | No silent default; propose optional explicit team default only if requested, and validate it belongs to the team's mapping | Checker, November 10 |
| STPC-D5: company scope | Map only categories compatible with the team's effective company and current record; no cross-company sharing in MVP | Thirdy + checker, November 10 |
| STPC-D6: incompatible changes | Require explicit valid category/stage replacement or block save; never silently reset existing opportunities | Checker, before UI work |
| STPC-D7: mapping removal | Block removal when used by active records until an explicit reassignment/migration is approved; keep historical references readable | Checker, before validation work |
| STPC-D8: constraint versus convenience | Treat approved team/category membership as a server-side business invariant, not merely a visual domain; it is not a record-access grant | Sir Roy + checker, November 10 |

Confirm how native automated assignment, lead conversion/merge, duplication and closed/archived historical records interact with D2–D8. Sign off a history policy rather than retroactively invalidating old records on unrelated writes.

## 4. Proposed data model and runtime design

### Data contract

Use the approved base category model (`crm.pipeline.category` is only a proposal). Reuse its active/company fields and CRM category relation; do not create a second category table.

| Proposed extension | Purpose |
| --- | --- |
| `pipeline_category_ids` on sales team | Many2many to base category model, maintained by authorized editors |
| `sales_team_ids` on category | Optional inverse view over the **same** relation table, not an independently stored list |
| Native team relation on CRM record | Source of team context; verify actual field and assignment lifecycle on Odoo 20 |
| Base category relation on CRM record | Selected category; validated against the team mapping when membership is enforced |
| Optional `default_pipeline_category_id` | Add only after STPC-D4 approval; never let it imply cross-company eligibility |

Finalize field naming and table/XML identifiers after the baseline gate. Proposed direct Many2many is sufficient for MVP; introduce an explicit mapping model only if approved per-mapping metadata (priority/default/effective dates) actually requires it.

### Selection and persistence policy

For a selected team, the eligible category set is the team's active mapped categories intersected with allowed company/access context. The eligible stage set is the selected category's approved stage mapping intersected with native team/company eligibility. No new record visibility is granted by either set.

- Both directions of configuration show the same relationship immediately after save/reopen.
- A category change or team change on an unsaved CRM form recomputes eligibility using current draft values. Do not auto-save or erase unrelated edits.
- Keep a compatible category/stage. For an incompatible value, show an actionable warning and require an explicit replacement before saving; the server must reject an inconsistent submitted combination.
- Protect normal form saves, supported quick-create, Kanban moves, lead conversion, batch operations and supported import/RPC paths. An onchange-only domain is not sufficient enforcement.
- Mapping edits that would affect existing opportunities must show an impact count/report respecting access rules and follow STPC-D7. Do not cascade changes to pipeline history.
- Do not let mapping administrators retrieve records they cannot otherwise read. A category is a classification, not a replacement for company/team security.
- Archived teams/categories are not choices for new assignments. Existing readable historical values remain legible; define which future transitions require replacement.
- If the generic filter module is installed later, compose with existing domains using intersection and nominate one owner for each field's filtering rule; never replace the native ACL/domain stack.

### Views, security, and suggested layout

Add a category relation to the native sales-team configuration and, if approved, the inverse team relation to category configuration. Add only necessary inherited CRM view changes. Check configuration groups/record rules with Thirdy and reuse the base module's security contract.

```text
addons/kpability_sales_team_pipeline_categories/
  __init__.py, __manifest__.py
  models/  (sales-team/category and CRM validation extensions)
  security/  (only additional privileges/rules actually required)
  views/  (sales team, category and CRM inherited views)
  tests/  (mapping, consistency, access and lifecycle cases)
  README.md
tests/e2e/sales-team-pipeline-categories.spec.*  (runner layout to confirm)
```

Proposed manifest dependency: approved category add-on, plus explicit native dependencies only where necessary. This branch is documentation-only; the dependency's implementation must be reviewed/landed into the agreed integration base before updating this consumer branch.

## 5. Work packages and schedule

| Date | Work package | Deliverable / gate |
| --- | --- | --- |
| November 10 | STPC-W1: shared Odoo baseline and D1–D8 decisions with category owner | Stable category/team/company contract and approved dependency integration sequence |
| November 11 | STPC-W2: implement relationship and configuration permissions | Both-direction round-trip tests; no duplicate category model |
| November 12 | STPC-W3: eligibility, invariant enforcement and migration checks | Form/quick-create/import paths agree; impact policy implemented |
| November 13 | STPC-W4: category-combined regression, reusable demo, evidence and checker review | All approved cases pass; delivery packet ready |

The same developer owns the category prerequisite due on the same date. Share fixtures/baseline work and escalate missing prerequisites immediately. Do not stack unreviewed module code into this feature PR merely to make its tests run.

## 6. Acceptance and verification matrix

Fixtures: companies A/B; editor and restricted sales users; teams Alpha/Beta; categories Shared/Alpha-only/Beta-only; native team-specific and shared stages; legacy unclassified and historical archived records. Expected results below are **not executed tests**.

| Case | Steps / condition | Expected acceptance result | Verification / visual proof |
| --- | --- | --- | --- |
| STPC-01 | Map Shared to Alpha and Beta; map Alpha-only to Alpha; reopen both configuration views | Many-to-many relation persists and inverse views agree | ORM relation tests + configuration screenshots |
| STPC-02 | Select Alpha then Beta on a new CRM record | Only approved active categories for that team/company are offered | Browser + team/category selection recording |
| STPC-03 | Select a category then inspect stages and Kanban | Category and native team restrictions intersect; no incompatible stage appears or saves | ORM + stage/board evidence |
| STPC-04 | Change team with compatible, then incompatible, category/stage | Compatible values remain; incompatible save is blocked until explicit replacement; no silent loss | Browser warning/save/reopen sequence + ORM |
| STPC-05 | Bypass UI with import/RPC or bulk updates | Approved membership/company invariant still enforced with useful errors | Backend tests + representative UI rejection/log reference |
| STPC-06 | Clear team, use a team with no mappings, and test a legacy unclassified record | D2/D3 policy holds; no fallback to all categories; native legacy flow preserved as approved | ORM + empty/missing-context evidence |
| STPC-07 | Remove a mapping used by active and historical records; archive a team/category | Impact policy blocks unsafe changes; history remains readable; new assignment excludes archived values | ORM + impact/archive evidence |
| STPC-08 | Edit mappings as sales user; switch company; submit foreign mapping/category | Configuration writes and foreign-company links denied; no visibility gained from mapping | Access tests + role/company recording |
| STPC-09 | Change team/category on dirty form then discard; repeat valid save | Discard restores persisted relations; saved values survive reload | Browser Save/Discard/reopen recording |
| STPC-10 | Exercise native lead conversion/merge, duplication, quick-create and automated assignment | Approved category/team policy is preserved or failure is explicit; native flow not broken | Integration tests + supported-flow recording |
| STPC-11 | Fresh install/upgrade with existing opportunities; configure another dataset | No forced remap or data loss; reusable without source/Studio changes | Lifecycle tests + second-configuration evidence |
| STPC-12 | Test with only category+team modules, then with generic filter/stage-rule consumers | Core feature independent of optional engines; combined eligibility/UX has one consistent outcome | Combined regression + recording |

For native paths unavailable in the approved edition, record the exact limitation and checker-approved applicability; do not silently mark them passed. Add lookup/query-count measurements on a representative number of teams, categories and opportunities; agree the budget before profiling.

## 7. Migration, release, risks, and readiness

- Inventory existing teams and category-like relations; propose an explicit mapping import. Never infer many-to-many links or a default from similarly named records.
- Generate a dry-run report of existing incompatible category/team/stage combinations. Approve migration and legacy exceptions before enabling new invariants; validate changes only where appropriate, not by blocking every unrelated historical edit.
- Follow shared staging/submodule release rules only when authorized. Record category module version compatibility and client pinning; rehearse install/upgrade and matching database/code restore.
- Primary risks: category prerequisite and shared deadline; ambiguous empty mapping behavior; companyless/global native teams; automated assignments rejected by a new invariant; configuration edits invalidating open records. Resolve via D2/D3/D5–D8 and end-to-end fixtures, not unrestricted fallbacks.

**Ready:** exact Odoo 20 baseline, approved category contract and D1–D8; agreed security/migration policy; dependency integration base and checker available.

**Done for future implementation:** STPC-01–STPC-12 and approved edge cases pass; both-direction configuration and reuse are demonstrated; install/upgrade/access checks pass; screenshots or recording map to feature cases; checker reproduces critical flows; limitations and rollback notes are documented. No implementation, publication or deployment is performed by this planning task.
