# Sales Team Pipeline Categories

An optional, standalone consumer of `kpability_pipeline_categories` for Odoo 20.
It adds explicit many-to-many sales-team eligibility without Studio, a second
category model, new roles, or category-based record access.

## Configure

1. Install `kpability_sales_team_pipeline_categories` with the repository root
   on the add-on path. Only the base category add-on is a dependency.
2. As a native **Sales Manager**, open **CRM → Configuration → Sales Teams**.
   On **Pipeline Categories**, explicitly map the team's permitted categories.
3. A company-specific team may map shared categories and its own company's
   categories. A companyless team may map shared categories only.
4. Review **CRM → Configuration → Pipeline → Pipeline Team Compatibility**
   before rollout. This read-only report includes archived records but respects
   the reader's CRM/category/team access and selected companies. Repeat for all
   relevant companies/users; an empty restricted report is not global clearance.
5. Explicitly add the required mappings or reclassify existing records in CRM.
   Installation and upgrades do **not** infer mappings, choose categories, reset
   stages, or backfill existing CRM records.

The category form shows the read-only **Sales Teams** inverse. All configuration
writes go through the team, including imports/RPC. No extra ACLs are necessary:
native team permissions and the base category record rules remain authoritative.

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

This delivery implements the **team foundation only**, as explicitly selected
on November 13, 2026 while PR #7 awaits review/merge. It neither restores nor
redesigns website/email intake. The approved `20` baseline (merged PR #4) still
contains its original intake code; this consumer cannot claim to disable it.
Do not enable that legacy categorized intake with this stricter consumer without
explicit valid team mappings. The separately reviewed cleanup must land first.

After PR #7 is approved and merged through `20`, the agreed follow-up is optional
`kpability_pipeline_email_intake` and `kpability_website_pipeline_intake` add-ons:
explicit website/category/team routes, company/team/category email deduplication,
opportunities-only custom intake, and opt-in legacy recovery. Neither add-on is
implemented or installed here. Issue #6 remains open.

See [implementation and verification](docs/sales-team-pipeline-categories.md)
for source baselines, commands, case coverage and outstanding release gates.
