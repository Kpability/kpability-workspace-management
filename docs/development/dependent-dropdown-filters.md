# Development plan: Dependent dropdown filters

| Item | Plan |
| --- | --- |
| Branch | `feature/dependent-dropdown-filters` |
| Target platform | Odoo 20 Community `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`; Enterprise `7773cfc038583d1b664491128424cd1904be946c`; locally verified, not release-certified |
| Owner / checker | Fyke / checker to confirm with Sir Roy |
| Source delivery target | November 17, 2026 (S1 p.2) |
| Status | Implemented November 15 and updated against default `20`; 30 dropdown + 50 approved pipeline/website checks pass on upgrade, 82 including framework on fresh install, plus 10 actual-Brave cases; independent review/release gates pending |
| Add-on family | `kpability_dependent_dropdown_filters`, `kpability_dependent_dropdown_crm_contacts`, `kpability_dependent_dropdown_hr` |

Read [shared standards](shared-standards.md) for source IDs S1–S4/U1, naming, ownership, security, PR evidence and deployment requirements. The original proposal below remains a planning record; this baseline and the [implementation record](../../kpability_dependent_dropdown_filters/docs/dependent-dropdown-filters.md) distinguish implemented scope from pending release gates.

## Implementation baseline — November 15, 2026

After authorizing implementation, the user explicitly approved:

- Adding CRM `customer_company_id` and Contacts `primary_contact_id`, preserving
  native CRM `partner_id`, `partner_name` and tenant `company_id`.
- Active non-company direct children only; missing parent means no choices;
  retain stale selections with a warning and explicit correction when changing
  the relationship. Unrelated unchanged legacy edits remain allowed.
- Intersect native domains and disable selector creation shortcuts.
- A maintained department record per tenant company, exact membership only,
  active internal users through active employees, subject to ordinary-user
  access verification and no new private-HR permissions.

These are implementation approvals, not independent checker/HR-owner sign-off
or authorization to deploy or activate company rules. The user subsequently
authorized committing, pushing and opening this feature PR, after updating it
against the default branch and retesting; reference PDFs must remain uncommitted.
Work is isolated on the existing `feature/dependent-dropdown-filters` branch in
`/tmp/opencode/kpability-dependent-dropdown-filters`, originally based on `fa14da4`.
The default branch is `20`, not `main`. Its fetched head `cf54708` (including
approved PR #4) was merged without conflicts in `0429dac`. The dirty sales-team
worktree is untouched; no unreviewed sibling feature was merged.

Source inspection of the exact Community checkout above confirms:

- Native CRM `partner_id` is a customer/contact Many2one; `partner_name` is text,
  not a selectable customer company. `company_id` is the tenant company.
   The approved CRM selector filters the existing Contact field; Contacts adds a
   company-only Primary Contact selector.
- Native CRM `user_id` selects internal users, not Sales-department employees.
  HR adds current-company employee relations and a public employee projection,
   with native internal-user read access to its public projection. The optional
   adapter uses that projection, not private employee records.
- Native domains already provide relational search/pagination. The gap is
  maintained, validated configuration, not a replacement search engine.
- Odoo 20 exposes `odoo.fields.Domain` and `models.Constraint`. Its web
  `Many2OneField` wraps `Many2One` through `computeM2OProps`; this is not the old
  widget API. No global web patch or `name_search` override is justified.

**Implementation:** a bounded code-registered binding catalog, maintained
per-tenant filter records, native computed JSON domains, native inherited forms,
and create/write validation of changed final relationships. No custom widget,
global search patch, executable configuration, automatic assignment, data
backfill, seeded filter, cache, or elevated resolver is introduced. Rules default
inactive. Internal users can read company-scoped runtime configuration;
administrators maintain it. Catalog bindings cannot be edited through normal
user permissions.

The optional HR adapter intersects the native internal-user/company domain with
an access-respecting `employee_public_ids any` predicate. Exact department
references are configurable; a department named “Sales” is not hard-coded.
Generic and CRM/Contacts installations do not require HR.

Native Odoo 20 company classification and CRM assignment recomputation remain
unchanged. On this exact build `res.partner.is_company` is computed from the
commercial-partner relationship and VAT; synthetic fixtures respect that rule.
Selecting a customer company does not force a tenant company or silently repair
an incompatible native assignment.

Installation, upgrades, backend tests and browser evidence use only newly
created `kpability_ddf_*` databases on the isolated localhost PostgreSQL fixture.
No company database is accessed. Exact results and remaining acceptance gaps are
recorded in the implementation record. Combined approved pipeline/website checks
pass; unmerged team/stage/shared-button integration, production-sized performance,
external integration compatibility, Odoo.sh/UAT and checker approval remain
release gates. The November 17 source date is not a new completion promise.

## 1. Objective and requirements

Provide a reusable, record-maintained way to narrow supported relational dropdowns from another field or approved configuration context, without Studio and without rewriting each client's XML domains.

| Requirement | Source | Interpretation |
| --- | --- | --- |
| DDF-R1: dependent dropdowns | S1 p.2 | Fyke target November 17; example individuals under a company. |
| DDF-R2: salesperson limited to Sales department | S3 p.2 | Determine eligible users from approved department/employee/user data, not an unexplained hard-coded list. |
| DDF-R3: individual limited to chosen company | S1 p.2; S3 p.2 | Clarify the parent-company/individual relationship and show it working. |
| DDF-R4: reusable record-maintained configuration | S1 p.2; S3 p.2; S2 pp.1–3 | Demonstrate CRM and Contacts reuse; final configuration-versus-XML coexistence needs approval. |
| DDF-R5: tested visual evidence | U1; S3 pp.3–4 | Screenshots or recording testing configuration, behavior and negative cases. |

The PDFs do not identify exact source/target fields, hierarchy semantics, missing-parent policy or backend enforcement scope. The following MVP makes those decisions explicit for approval.

## 2. Scope and decisions

### In scope

- Privileged record-based configuration for approved model/Many2one field pairs and bounded dependent filters.
- Two initial adapters: **company -> individual** and **Sales-department context -> eligible salesperson user**.
- Consistent filtering in the supported form's autocomplete and Search More paths, respecting existing native domains, record rules and company restrictions.
- Recompute on draft-parent changes, handle stale child selections and Save/Discard safely, and validate explicitly approved business invariants server-side.
- CRM and Contacts demonstrations using actual approved fields on the Odoo 20 build. If a demonstration needs a new field/view, obtain approval before adding it; do not invent a native Contacts salesperson/contact pairing.
- Configuration validation, basic explainability, access tests, performance checks and lifecycle/reuse documentation.

### Out of scope unless approved

An arbitrary query builder, executable expressions, all widgets/views, Many2many/One2many widgets, multi-hop chains/cascades, external APIs, territory/auto-assignment, HR data model redesign, RBAC redesign and replacing every native XML domain. Team/category MVP remains independent of this later module.

| Decision | Proposed default | Approval / gate |
| --- | --- | --- |
| DDF-D1: exact field/view mapping | Inspect CRM and Contacts and select existing supported Many2one fields where possible; document any proposed added field | Fyke + checker, early baseline; freeze before November 16 |
| DDF-D2: company hierarchy | Individuals are active non-company direct children of the selected company, intersected with native company/security policy; include descendants/commercial hierarchy only if requested | Sir Roy/checker, before adapter work |
| DDF-D3: missing parent / no match | No new child choices; display a clear select-parent/no-match hint, not an unrestricted fallback. Preserve readable legacy values until the approved edit/migration policy applies | Checker, before engine work |
| DDF-D4: stale child after parent change | Preserve the draft value with an invalid-selection warning, require explicit clear/reselection before save; no silent discard/auto-save | Checker, before UI work |
| DDF-D5: Sales department identity | Maintained department reference per applicable company, not text matching on a department name. Confirm descendant-department membership policy | Sir Roy + HR/data owner, before HR adapter |
| DDF-D6: employee-to-user mapping | Only active, eligible internal salesperson users linked through the approved current-company employee/department relation; define multiple-employee and missing-user cases | HR owner + Thirdy/checker, before implementation |
| DDF-D7: enforcement | Domains are a selection aid, not security. Enforce parent/child or department membership server-side only where approved as a business invariant | Sir Roy + Thirdy/checker, before validation work |
| DDF-D8: native domains/configuration | Intersect supported configured/native domains; records maintain the dependency, while minimal XML/adapters still declare supported fields/views | Checker, before frontend design |
| DDF-D9: create flows | Disable unsupported quick-create/create-and-edit for constrained selectors unless the new record can inherit/validate its parent safely | Checker, before UI integration |

If HR is not installed or ordinary sales users cannot lawfully access the necessary mapping, mark the Sales-department adapter blocked pending an approved secured mapping design. A Sales security group is not automatically equivalent to an HR Sales department; never substitute silently.

## 3. Proposed architecture and data model

### Configuration engine

First inspect native Odoo 20 domain/context/onchange support. Use native mechanisms where sufficient, adding only the reusable configuration/resolution gap. Prefer a limited engine with a clear supported surface to a fragile global patch.

Proposed grouped model `dropdown.filters` / `DropdownFilters`:

| Proposed configuration | Purpose |
| --- | --- |
| `s_name`, `active`, `company_id` | Human-readable identity, controlled activation and company scope |
| Approved target-model and child-field references | Constrain the field being filtered; validate a supported Many2one relation |
| Approved parent-field or context-provider reference | Read the current draft parent or maintained department context |
| Approved adapter / lookup reference | Select a maintained adapter record, not arbitrary executable code |
| Bounded relation/condition records | Describe supported field equality/membership with typed references and operators |
| Optional documented behavior settings | Only add approved missing-parent/stale-value/enforcement options; avoid per-client uncontrolled branches |

Validate field types, related-model compatibility, company scope, duplicate/conflicting active rules and unsupported dependency cycles before activation. Store references to allowed metadata/lookup records, not freely typed technical names or strings evaluated as code. Prefer deterministic composition: native domain AND every applicable approved filter. Reject conflicting configuration or explain an empty intersection; never OR it into a broader set silently.

### Initial adapter contracts

**A. Company -> individual**

- Inspect `res.partner` and actual CRM/Contacts fields, native domain, company hierarchy and archive behavior on Odoo 20.
- Derive the selected parent from the unsaved form, not a stale saved record. Apply the approved individual/direct-parent predicate, current access/company restrictions and any native field domain.
- Do not globally alter all partner searches. Scope the resolver to approved dependent fields/views/context so unrelated partner lookups retain native behavior.
- Existing archived/inaccessible child values follow the approved historical display/access policy. Never use elevated access merely to show a forbidden label.

**B. Sales-department context -> salesperson**

- Verify candidate `hr.department`, `hr.employee`, `res.users` relations and native salesperson eligibility on the actual build. These are inspection targets, not guaranteed schemas.
- Resolve the configured company-specific Sales department to eligible employees/users, with the approved descendants and multiple-employee policy. Exclude inactive users/employees, portal/share users and users not otherwise eligible under the native salesperson domain.
- Keep HR optional to the generic engine. A dedicated adapter may depend on `hr` after approval; generic/Contacts use must install without HR.
- Use a supported public employee projection if it exposes the approved mapping safely, or design a tightly authorized minimal resolver with Thirdy/HR. Do not grant broad private employee access or use unrestricted `sudo`. Return only what the user is allowed to select, not HR details.
- If no approved mapping/department exists, show a configuration/no-match condition rather than returning all users.

### Runtime, UI, and persistence

1. Load applicable authorized configuration for model/field/company and obtain allowed parent/context values.
2. Compose the configured filter with native domains and security. Prefer native server-side filtered search/pagination; avoid fetching all contacts/users to filter in JavaScript or sending huge unrestricted ID lists.
3. Apply identical semantics to autocomplete and Search More. Handle quick-create/create-and-edit per DDF-D9 so a new record cannot bypass the selected relation.
4. Recompute when draft dependencies change. Guard against stale asynchronous responses when users change parents quickly; only the latest parent/context result applies.
5. On incompatible child selection, follow DDF-D4. Preserve unrelated draft edits. A new unsaved parent without a usable ID offers no persisted children until a supported create flow completes; do not auto-save the whole form.
6. Save only an approved valid relation; discard restores saved parent/child and eligibility. For approved invariants, validate supported create/write/import/RPC paths as well, with legacy/unchanged-value policy signed off.
7. Preserve ACLs/record rules and native company behavior. Filtering options does not grant access and is not proof that a user cannot reach records elsewhere.

Use verified Odoo 20 field/search/form hooks, not a global `name_search` override or an assumed old-version modifier API. Scope caches by relevant user/company/configuration and invalidate after configuration, department or membership changes. Errors and hints must be translatable, keyboard-accessible and not leak inaccessible record names.

### Proposed implementation layout (not created)

```text
addons/kpability_dependent_dropdown_filters/
  models/, security/, views/, static/src/, tests/, README.md
  __init__.py, __manifest__.py
addons/kpability_dependent_dropdown_crm_contacts/  (if approved split)
  models/, views/, tests/, README.md
  __init__.py, __manifest__.py
addons/kpability_dependent_dropdown_hr/  (optional approved adapter)
  models/, security/, views/, tests/, README.md
  __init__.py, __manifest__.py
tests/e2e/dependent-dropdown-filters.spec.*  (runner layout to confirm)
```

Finalize packaging and dependencies after DDF-D1. A generic engine must not accidentally force CRM or private HR dependencies into every client. It also must not overwrite category/team selection logic already owned by the November 13 modules.

## 4. Work packages and schedule

| Date | Work package | Deliverable / gate |
| --- | --- | --- |
| November 10–13 | DDF-W1: baseline questions, field-pair selection, HR/access review and D1–D9 decisions alongside earlier modules | Approved limited support matrix, adapter inputs and test fixtures before build window |
| November 16 | DDF-W2: configuration/resolver, CRM/Contacts and approved HR adapter, draft-state and search integration | Initial happy/negative cases reproducible; native domains preserved |
| November 17 | DDF-W3: backend invariants, security/lifecycle/performance regression, reuse/evidence and checker demo | Approved cases pass and delivery packet ready for source target |
| November 25 | DDF-W4: align browser cases with TJ's standardized Playwright setup if not ready earlier | Tooling follow-up only; November 17 tests/evidence remain required |

The short build window assumes native mechanisms, a narrow MVP and approved HR access beforehand. Estimate after baseline; escalate if two adapters and a new engine cannot be responsibly delivered in this window. Any adapter deferral or date change needs explicit approval, not a silent substitute or dropped test coverage.

## 5. Acceptance and verification matrix

Fixtures: companies A/B, company partners with individuals, unrelated and archived partners; departments Sales/Other, eligible and ineligible employees/users, portal/inactive/no-linked-user examples; editor and restricted sales user. Map exact native/added field names after DDF-D1. Cases below are **planned, not executed**.

| Case | Steps / condition | Expected acceptance result | Verification / visual proof |
| --- | --- | --- | --- |
| DDF-01 | Editor configures an approved filter; ordinary user tries editing configuration | Configuration persists; unauthorized edits rejected; no Studio/code edit required | ORM/access tests + setup/denial screenshots |
| DDF-02 | Select company A then company B on CRM's approved field pair | Autocomplete and Search More offer only eligible individuals for current draft parent | Browser + parent/child search recording |
| DDF-03 | Reuse maintained config on approved Contacts field pair | Same dependency principle works without a client-specific code change | Browser + Contacts/reuse recording |
| DDF-04 | Open form with no parent, no matches, archived or inaccessible child values | D3/history policy applies; clear hints; no fallback to all records or leaked labels | ORM/access + empty/archived-state evidence |
| DDF-05 | Pick a child then change/clear parent, including rapid successive changes | Stale selection warned; explicit repair before save; no stale search response or lost draft edits | Browser race/stale-value recording |
| DDF-06 | Save/discard changed parent and child; reopen | Valid save persists; discard restores both values and native/domain state | Browser Save/Discard/reopen sequence |
| DDF-07 | Configure Sales department and inspect salesperson options | Only approved active internal eligible users from mapped department/company appear | Resolver tests + department/user selection recording |
| DDF-08 | Change department membership; test no linked user, multiple employees, portal/inactive users and no HR | D5/D6 and optional-dependency policy apply; safe cache invalidation; no private HR exposure | ORM/access/install tests + negative/configuration proof |
| DDF-09 | Use native restrictive domain, switch company/role, attempt direct foreign assignment | Configured filter intersects native domain; ACL/company boundaries remain; approved invariants reject bypasses | ORM/import/RPC tests + representative role/error evidence |
| DDF-10 | Attempt quick-create/create-and-edit and unsupported widgets/config cycles | Approved safe create behavior or explicit unsupported state; invalid config rejected | Browser/config tests + safe-create/error proof |
| DDF-11 | Fresh install/upgrade, disable filter, configure another dataset | Native behavior preserved when no rule; no record loss; reusable without source/Studio changes | Lifecycle tests + second-config recording |
| DDF-12 | Combine with category/team and stage rules; disable optional adapters | One consistent domain owner per field; required/read-only/disabled state and selection do not conflict; generic engine works without HR/CRM adapters | Combined integration + supported-flow evidence |

Measure lookup query count, pagination and response time with a representative contact/user/employee dataset; agree record counts and latency budget before profiling. Include searches with zero/many results and repeated parent changes. A small fixture passing is not a performance claim.

## 6. Migration, release, risks, and readiness

- Activate no custom filter until field pairs, privacy and D1–D9 are approved. Inventory existing XML/domain overrides and designate one composition owner; do not delete unknown custom behavior.
- Report existing parent/child or salesperson/department mismatches. Agree grandfathering versus correction before enforcing invariants; unrelated edits to historical records must follow that explicit policy.
- Validate metadata links/configuration on upgrade. Deactivation should restore native selection behavior, not alter existing records. Approved business-invariant removal/migration requires separate review.
- Follow shared sample/staging/submodule pinning and backup/restore gates only when release is authorized. Version HR/native adapters compatibly with the engine and record the exact tested module set.
- Key risks: unverified field/widget APIs, strict company hierarchy assumptions, HR privacy and edition dependencies, asynchronous stale results, quick-create bypasses, huge ID lists and hidden-required conflicts with stage rules. Use D1–D9, bounded native searches and the combined matrix to mitigate them.

**Ready:** exact Odoo 20 build and field/view support recorded; D1–D9 approved; HR permission/data contract and configuration/native-domain policy settled; fixtures, checker and test instance available.

**Done for future implementation:** DDF-01–DDF-12 and approved edge cases pass; both source examples and CRM/Contacts reuse demonstrated; no broad HR/security grants; install/upgrade/performance results recorded; screenshots or recording map to feature cases and checker reproduces critical paths. No code, live testing, PR publication or deployment is performed by this planning task.
