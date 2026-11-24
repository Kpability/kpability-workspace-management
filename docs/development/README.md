# Odoo 20 module development plans

**Prepared:** November 10, 2026 · **Implementation started:** November 11, 2026 · **Developer:** Fyke

These documents describe reusable Odoo 20 modules. Pipeline Categories is now implemented on this branch; see its [implementation and verification record](../../kpability_pipeline_categories/docs/pipeline-categories.md) for local Odoo 20 Enterprise results and outstanding release gates. Other feature documents remain plans. Planning itself did not certify any module.

## One branch per module

Each feature branch contains its own plan plus the same shared standards and PR template. Switch to the relevant local branch to read its plan; the other module plans are intentionally not included on that branch.

| Local branch | Plan path | Source target date |
| --- | --- | --- |
| `feature/pipeline-categories` | `kpability_pipeline_categories/docs/pipeline-categories.md` | November 13, 2026 |
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

Arrows mean prerequisite to consumer. The category add-on now depends only on `crm`; other arrows remain proposed. Business workflows must still work with each optional engine absent.

The category and team branches remain independent local branches. During implementation, land the category dependency into the agreed integration base before updating the team branch; do not silently make a PR depend on unreviewed sibling-branch commits.

## Planning versus implementation

- Source assignments and dates are recorded, not newly promised delivery commitments.
- Suggested architecture, field names, edge-case defaults, and daily milestones require reviewer approval.
- Odoo 20 is the requested target. Availability of a branch named `20` is not proof of runtime or API compatibility.
- The initial planning checkout contained IDE metadata only. This branch now includes PR #1's `workspace_management` and the standalone `kpability_pipeline_categories` add-on. The Odoo server and Enterprise sources are sibling checkouts, not vendored into this repository.
- Do not create a release, configure Odoo.sh, add real submodules, open a PR, or push these planning changes without separate authorization.
