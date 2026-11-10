# Odoo 20 module development plans

**Status:** proposed plans only · **Prepared:** November 10, 2026 · **Developer:** Fyke

These documents plan reusable Odoo 20 modules; they do not implement or certify them. No Odoo instance, module tests, screenshots, or recordings were produced during planning.

## One branch per module

Each feature branch contains its own plan plus the same shared standards and PR template. Switch to the relevant local branch to read its plan; the other module plans are intentionally not included on that branch.

| Local branch | Plan path | Source target date |
| --- | --- | --- |
| `feature/pipeline-categories` | `docs/development/pipeline-categories.md` | November 13, 2026 |
| `feature/sales-team-pipeline-categories` | `docs/development/sales-team-pipeline-categories.md` | November 13, 2026 |
| `feature/stage-rules` | `docs/development/stage-rules.md` | November 23, 2026 |
| `feature/dependent-dropdown-filters` | `docs/development/dependent-dropdown-filters.md` | November 17, 2026 |

Start with [shared standards and delivery](shared-standards.md). The proposed PR form is [`.github/pull_request_template.md`](../../.github/pull_request_template.md).

## Delivery sequence and module boundaries

1. **Pipeline categories:** maintain category records and their CRM/stage relationships.
2. **Sales team pipeline categories:** own the many-to-many team/category mapping and team-dependent selection policy; depend on the category module, not the reverse.
3. **Dependent dropdown filters:** deliver a reusable filtering mechanism with salesperson-by-department and individual-by-company adapters. This must not become a prerequisite for the November 13 category delivery.
4. **Stage rules:** deliver configurable field presentation by stage, with conditional/role-aware behavior and Save/Discard integration. Category-specific integration must not couple the generic rule engine to CRM unnecessarily.

Proposed dependency direction:

```text
crm -> pipeline categories -> sales team pipeline categories
base/web -> dependent dropdown engine -> CRM/Contacts adapters (+ hr if approved)
base/web -> stage-rule engine -> CRM adapter -> pipeline categories (if category scoping approved)
approved shared Save/Discard module -> stage-rule UX integration
```

Arrows mean prerequisite to consumer. Add-on splitting and exact dependencies require an Odoo 20 baseline review; this is not an existing manifest graph. Business workflows must still work with each optional engine absent.

The category and team branches remain independent local branches. During implementation, land the category dependency into the agreed integration base before updating the team branch; do not silently make a PR depend on unreviewed sibling-branch commits.

## Planning versus implementation

- Source assignments and dates are recorded, not newly promised delivery commitments.
- Suggested architecture, field names, edge-case defaults, and daily milestones require reviewer approval.
- Odoo 20 is the requested target. Availability of a branch named `20` is not proof of runtime or API compatibility.
- This checkout initially contains tracked IDE metadata only, not Odoo server code or custom add-ons. Existing local branches share initial commit `b16246c`; no local `staging` branch was found.
- Do not create a release, configure Odoo.sh, add real submodules, open a PR, or push these planning changes without separate authorization.
