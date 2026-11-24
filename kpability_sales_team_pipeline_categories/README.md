# Sales Team Pipeline Categories

An optional, standalone consumer of `kpability_pipeline_categories` for Odoo 20.
It adds explicit many-to-many sales-team eligibility without Studio, a second
category model, new roles, or category-based record access.

## Configure

1. Install `kpability_sales_team_pipeline_categories` with the repository root
   on the add-on path. Only the base category add-on is a dependency.
2. As a native **Sales Manager**, open **CRM → Configuration → Sales Teams**.
   On **Pipeline Categories**, explicitly map the team's permitted categories.
   The equivalent **Sales Teams** field on
   **CRM → Configuration → Pipeline → Pipeline Categories** edits the same
   mapping from the category side.
3. A company-specific team may map shared categories and its own company's
   categories. A companyless team may map shared categories only.
4. Review **CRM → Configuration → Pipeline → Pipeline Team Compatibility**
   before rollout. This read-only report includes archived records but respects
   the reader's CRM/category/team access and selected companies. Repeat for all
   relevant companies/users; an empty restricted report is not global clearance.
5. Explicitly add the required mappings or reclassify existing records in CRM.
   Installation and upgrades do **not** infer mappings, choose categories, reset
   stages, or backfill existing CRM records.

The category form also lets Sales Managers add or remove **Sales Teams**. Both
forms edit the same relation, and category-side writes are routed through the
team field, so its active-category, company-scope and used-history protections
still apply. The picker only offers teams compatible with the category's
company, and a company-scope change can be saved together with a compatible
mapping swap. Defaults take the same checked path, and an explicit empty
selection overrides them. The field is read-only for non-managers. Actual
writes still require native team write permissions; imports/RPC use the same
checks. No extra ACLs are necessary: native team write permissions and the base
category record rules remain authoritative.

## CRM behavior

- Category remains optional. Missing team or empty mappings mean **no new
  categorized assignments**, not unrestricted categories.
- The Category dropdown intersects active mapped categories with company and
  access rules. Stages still intersect category mappings and native team rules.
- Changing a team never clears/replaces the category automatically. Invalid
  saves, imports, RPC and bulk writes are rejected. Explicitly replace/clear the
  category or choose a compatible team.
- Native team/user/company/stage recomputation, Won/Lost, conversion, merge,
  assignment and duplication are retained. A native team change can recompute
  the stage; this module does not freeze native stages.
- Quick-create exposes **Sales Team**, including on category-scoped boards, so
  an incompatible hidden native default can be corrected before saving.
- Archiving preserves mappings and history. Archived teams/categories cannot
  receive new categorized assignments. Existing historical references and
  unrelated edits remain possible.
- Removing used mappings, narrowing company scope, or deleting a used team is
  blocked for **all** categorized history, including archived and Won/Lost
  records. Explicit reclassification is required. Hidden usage produces only a
  generic error, never record names, IDs or counts.
- Legacy invalid combinations are not silently repaired. Unrelated edits remain
  allowed, but changing their routing/stage requires a valid final combination.
  Add missing mappings incrementally using the compatibility report.

## Intake dependency gate

This delivery implements the **team foundation only**. Merged PR #4 provides
the category dependency, so review can proceed independently of
[PR #7](https://github.com/Kpability/kpability-workspace-management/pull/7).
The original categorized website/email intake can create records without a
mapped team; this add-on does not disable those routes. **Do not enable this
add-on alongside legacy categorized intake.** For rollout, wait for PR #7 to
merge through `20`, apply its retirement upgrades (do not uninstall the legacy
companion), and smoke-test the resulting staging build before enabling.

Optional replacement website/email add-ons and explicit recovery of legacy
configuration remain separate work tracked in
[issue #6](https://github.com/Kpability/kpability-workspace-management/issues/6);
they are not part of this add-on or a prerequisite for the team foundation.

See [implementation and verification](docs/sales-team-pipeline-categories.md)
for source baselines, commands, case coverage and outstanding release gates.
