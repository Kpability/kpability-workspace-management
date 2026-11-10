# Development plan: Pipeline categories

| Item | Plan |
| --- | --- |
| Branch | `feature/pipeline-categories` |
| Target platform | Odoo 20; exact build and APIs unverified |
| Owner / checker | Fyke / checker to confirm with Sir Roy |
| Source delivery target | November 13, 2026 (S1 p.1) |
| Status | Proposed development plan only; no implementation or tests performed |
| Proposed add-on | `kpability_pipeline_categories` |

Read [shared standards](shared-standards.md) for source definitions S1–S4/U1, ownership conflicts, PR evidence, security, release and rollback requirements. Technical names below are proposals, not existing repository objects.

## 1. Objective and source-backed requirements

Provide reusable, record-configured CRM pipeline categories without Studio. Give the team-category and stage-rule modules a stable category contract without embedding their logic in this base module.

| Requirement | Source | Interpretation |
| --- | --- | --- |
| PC-R1: standardize pipeline categories | S1 p.1; S4 p.1 | Deliver category configuration and an approved CRM integration. Exact native gap needs baseline review. |
| PC-R2: support the team/category design | S4 p.1 | Multiple teams/categories were discussed; the team module owns that relationship. Final design needs approval. |
| PC-R3: reusable, maintainable lookups | S1 p.2; S2 pp.1–3 | Maintain categories as records, not a fixed selection or client-specific code. |
| PC-R4: no Studio; naming standards | S1 pp.1–2 | Standard installable module with approved naming. |
| PC-R5: visible test proof per feature PR | U1; S3 pp.3–4 | Attach case-linked screenshots or recording and obtain checker review. |

The PDFs do not specify stage/category cardinality, defaults, migration, or whether category selection is mandatory. The following baseline is a concrete proposal for approval, not a claim that those details were decided in the meetings.

## 2. Scope and proposed functional contract

### In scope

- Category list/form configuration with descriptive label, description, display ordering, active/archive state and company ownership.
- Proposed CRM integration: one optional category per lead/opportunity, displayed in supported CRM forms and available for search/group-by where supported.
- Proposed stage integration: an explicit many-to-many category/stage mapping, allowing a shared stage in several categories. Confirm this against a simpler exclusive-stage alternative before building it.
- Applicable stage choices and Kanban columns follow the selected category, while retaining native team restrictions and access rules. Changing a dropdown alone is insufficient if Kanban still exposes incompatible stages.
- Configuration permissions, relationship consistency, safe archive/removal and a migration procedure.
- A stable category relation consumed by the separate team module. Install and use the category module without that consumer.

### Out of scope

- Team/category mapping and team-dependent selection, owned by `feature/sales-team-pipeline-categories`.
- Field visible/enabled/required rules, generic dropdown engine, territory/auto-assignment, activity/email templates, won/lost reasons, company RBAC/menu redesign and global Save/Discard implementation.
- Changing native Won/Lost semantics or lead-feature enablement. No forced lead-feature activation.

### Proposed user journeys

1. Authorized configuration editor creates categories **New Business** and **Renewals**, with different ordered stage mappings, using records only.
2. Sales user selects a category on a CRM record and sees the matching stages in the agreed form/Kanban paths.
3. User searches/groups records by category; changing the category preserves existing work unless the user explicitly confirms a valid transition.
4. Editor archives a category: it remains readable on historical records but is not offered for new assignments.
5. The same add-on supports a second dataset/company configuration without source edits or Studio.

## 3. Odoo 20 discovery and decisions required

Complete the shared baseline gate, then record the checker-approved answers:

| Decision | Proposed default | Approver / timing |
| --- | --- | --- |
| PC-D1: native versus custom category | Reuse a native equivalent if it meets all approved cases; otherwise add a custom model | Fyke + checker, November 10 |
| PC-D2: category/stage cardinality | One category per CRM record; stages reusable through an explicit many-to-many mapping | Sir Roy/checker, November 10 |
| PC-D3: no category / unmapped stages | Allow legacy/unclassified records during rollout; preserve native behavior when no category is set; an unmapped stage is not implicitly global for categorized records | Checker, November 10 |
| PC-D4: company ownership | Company-specific categories for MVP; no globally shared category until cross-company policy is approved | Thirdy + checker, November 10 |
| PC-D5: mandatory selection/default | No mandatory category or silent default until migration/client policy is signed off | Sir Roy/checker, November 10 |
| PC-D6: invalid category/stage change | Reject inconsistent saved combinations with a clear error; prompt for a compatible stage rather than silently resetting it | Checker, before UI work |
| PC-D7: uniqueness and removal | Normalized label unique within a company; archive preferred; block deletion if referenced | Checker, before schema freeze |

If the approved scope does not include category-specific stages, explicitly revise PC-R1's interpretation and PC-03/PC-04 before implementation. Do not ship an undocumented stage policy.

## 4. Proposed technical design

### Data and relations

Inspect candidate native `crm.lead`, `crm.stage`, and `crm.team` behavior on the actual Odoo 20 build. Preserve native lifecycle/team behavior rather than replacing CRM.

| Proposed object/field | Type / purpose |
| --- | --- |
| `crm.pipeline.category` / `CrmPipelineCategory` | Custom category lookup only if no suitable native concept exists |
| `s_name` | Required translatable text label; configure display-name handling explicitly |
| `s_description` | Optional descriptive text |
| `n_sequence` | Numeric sort priority, with a deterministic tie-breaker |
| `active` | Archive flag; historical references remain intact |
| `company_id` | Company ownership; company-aware access and consistency checks |
| `pipeline_category_id` on CRM record | Many2one category; optional during migration; deletion restricted |
| `pipeline_category_ids` on stage | Proposed Many2many stage applicability, subject to PC-D2 |

The team consumer adds its own team/category mapping; the base add-on must not require it. Native team applicability, stage company behavior and any native Won stage properties remain constraints on the effective stage set. A stage's category mapping must not broaden its existing team/company eligibility.

### Runtime and UI behavior

- Add configuration menus only for authorized editors; ordinary CRM users receive the necessary category read access, not automatic configuration write access. Coordinate final groups with Thirdy.
- Add inherited form/search/Kanban integration using verified Odoo 20 extension points. Define whether mixed-category boards require a category filter or a supported combined layout; do not assume one board can represent incompatible stage sequences.
- Determine effective stages from category mapping intersected with native eligibility. Revalidate saved category/stage combinations through ORM logic, including direct stage drag/drop and supported imports/RPC.
- Category changes on dirty forms must not auto-save or silently discard unrelated changes. If the current stage is incompatible, require an explicit replacement or block saving with an actionable message.
- For approved category/team constraints, expose a small category-selection integration contract to the consumer; do not build a generic dropdown engine here or introduce a circular dependency.
- Validate stage-mapping edits against existing records. Prefer blocking removal of a used mapping with an impact report until records are explicitly remapped; never move historical records silently.
- Audit configuration changes using the target's available standard mechanism; confirm whether chatter is needed instead of adding an unnecessary dependency.

### Proposed implementation layout (not created by this task)

```text
addons/kpability_pipeline_categories/
  __init__.py, __manifest__.py
  models/  (category and CRM/stage extensions)
  security/  (configuration ACLs and company rules)
  views/  (category, CRM, stage and search views)
  tests/  (ORM, access, lifecycle and integration cases)
  README.md
tests/e2e/pipeline-categories.spec.*  (runner layout to confirm)
```

Proposed dependency: `crm` plus only demonstrated requirements. Version, license, external IDs, constraint APIs and any web assets are finalized at the baseline gate.

## 5. Implementation work packages and dates

| Date | Work package | Deliverable / exit gate |
| --- | --- | --- |
| November 10 | PC-W1: inspect native behavior, agree PC-D1–D7 and consumer contract | Approved relationship diagram, stage policy, company policy and actual base branch |
| November 11 | PC-W2: scaffold category lookup, relations, ACLs and validation | Fresh install; model/access tests; stable consumer field contract |
| November 12 | PC-W3: configuration/forms/search/Kanban, dirty-form behavior and migration rehearsal | PC-01–PC-08 reproducible on sample data; team consumer can integrate |
| November 13 | PC-W4: lifecycle, combined regression, evidence and checker demo | All approved cases pass; visual proof, configuration guide and PR packet ready |

This overlaps the team module's deadline. Share the baseline/fixtures and review the combined flow on November 13. Escalate missing Odoo access or unsigned stage semantics rather than bypassing tests to meet the date.

## 6. Acceptance and verification matrix

Use synthetic companies A/B, an authorized editor, a normal sales user, and a user without configuration privileges. Create two categories with an overlapping and a category-only stage. All results below are expected outcomes, **not executed tests**.

| Case | Steps / condition | Expected acceptance result | Verification / visual proof |
| --- | --- | --- | --- |
| PC-01 | Editor creates, edits and reorders two categories; sales user opens them | Labels/order persist; sales user cannot edit configuration | ORM ACL tests + configuration screenshots/recording |
| PC-02 | Create a duplicate label in the same company and a label in company B | Approved uniqueness policy enforced without cross-company data disclosure | ORM validation + visible error |
| PC-03 | Select each category in CRM form and open its pipeline | Applicable stage choices/columns match approved mapping and native restrictions | Browser + before/after category/stage evidence |
| PC-04 | Change category or drag record into an incompatible stage; repeat by import/RPC | No inconsistent saved pair or silent stage reset; clear errors | ORM + browser invalid-change recording |
| PC-05 | Filter/group CRM records by category; refresh/reopen | Saved classification and counts remain correct without exposing inaccessible records | Browser + search/group/reopen evidence |
| PC-06 | Archive a used category; attempt new assignment and deletion | Historical value still readable; no new archived assignment; referenced delete blocked | ORM + archive/history proof |
| PC-07 | Switch companies/users and attempt foreign-company category assignment | No unauthorized lookup or assignment; native record security unchanged | ORM access + role/company recording |
| PC-08 | Edit category/stage on a dirty form, then discard; repeat save | Discard restores persisted values; valid save persists; unrelated edits not lost | Browser Save/Discard/reopen recording |
| PC-09 | Install without team/filter/stage-rule modules; keep leads disabled, then test leads enabled | Base module works independently in both native lead configurations | Fresh-install tests + supported-flow evidence |
| PC-10 | Upgrade representative unclassified/legacy records; remove a used stage mapping | No record loss/auto-classification; mapping edit follows approved impact policy | Lifecycle tests + migration report and UI check |
| PC-11 | Configure a second category dataset; integrate the team consumer | Reuse without code/Studio; team narrowing does not broaden stage access | Combined test + reuse recording |

PC-03/PC-04 require PC-D2 approval. Before implementation, expand fixtures for empty categories, no eligible stages, archived stages, native Won/Lost and bulk operations. Measure category/stage lookup and grouped-board behavior on an agreed representative record count, including query growth; set thresholds with the checker before profiling.

## 7. Migration, rollout, and support

- Inventory existing stage/team usage and any category-like native/custom fields. Produce a dry-run mapping report; do not overwrite existing data or infer categories from names.
- For initial installation, retain unclassified history and native behavior until an explicit backfill is approved. If mandatory categories are later requested, backfill and validate before tightening constraints.
- Use restricted deletion for referenced categories and archive for retirement. Define whether reusing archived labels is allowed in PC-D7.
- Rehearse fresh install and upgrade with historical records, including access checks after archiving. Record the exact module commit and dataset.
- Follow the shared reusable-module/submodule staging workflow when release is authorized. Rollback requires a verified database/code pair; a field or relation change may not be reversible by code alone.

## 8. Definition of ready and done

**Ready:** Odoo 20 baseline recorded; PC-D1–D7 approved; Thirdy access contract and team-consumer contract agreed; staging/version base resolved; sample data and checker available.

**Done for future implementation:** PC-01–PC-11 and approved edge cases pass on the named Odoo 20 build; install/upgrade/security checks pass; configuration and reuse instructions exist; screenshots or recording map to each feature case; checker reproduces core flows; known limitations/migration/rollback are documented. No GitHub publication or deployment is part of this planning task.
