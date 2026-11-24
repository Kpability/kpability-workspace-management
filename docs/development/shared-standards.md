# Shared implementation and delivery standards

**Status:** planning proposal · **Target:** Odoo 20 · **Prepared:** November 10, 2026

## 1. Sources, precedence, and traceability

References were read from `/run/media/fyke/android/DocumentsLinux/Work/Kpability/`. Page numbers below are physical PDF pages. The source PDFs remain external and are not copied into this repository.

| ID | Document | Relevant source content |
| --- | --- | --- |
| S1 | `Standard Implementation Considerations with Timelinepdf.pdf` | p.1: no Studio; category/team-category targets November 13; stage rules November 23; Thirdy owns RBAC/menu work; TJ owns territory, reasons, and templates. p.2: naming, model-backed lookups, Thirdy's Save/Discard target November 13, dropdown target November 17, Playwright standardization target November 25. |
| S2 | `Odoo Submodules.pdf` | pp.1–3: central reusable modules, independent client repositories, tested feature branches. p.4: example version branch `20`. pp.5–9: private-repository deploy-key setup and rebuilding on Odoo.sh. p.10: activation/testing, including an existing Save/Discard example. p.11: client staging before production. p.12 asks about updates but does not define a full update procedure. |
| S3 | `Odoo Standardization - Fyke Focus.pdf` | pp.1–2: configurable front-end stage rules; reuse/certification; naming; salesperson-by-Sales-department and individuals-by-company dropdowns; clearer Save/Discard. pp.2–3: territory boundary/ownership questions and backend-versus-frontend distinction. pp.3–4: unresolved scope, explicit dates, staging-based branch workflow, recording proof and maker/checker review. These are personal transcription notes, with confirmation flags. |
| S4 | `Odoo Standardization.pdf` (optional cross-check) | p.1: team/category many-to-many discussed, final category design and native-version capabilities still to confirm. p.2: company-centric access, naming, Save/Discard, configurable dropdowns and Playwright. p.3: assignments/workflow require confirmation. |
| U1 | User request for this planning task | Odoo 20; documentation only; one named branch per module; local work only; future PRs must include screenshots or a screen recording testing the module and its features; a custom PR template is permitted. |

Apply U1 to this task's scope/version/PR evidence. Use S1 for explicit target dates and the working ownership baseline. Use S2 for reuse/deployment principles. S3/S4 supply context, not authority to silently expand scope. Record conflicting or unconfirmed items rather than choosing an undocumented requirement.

### Ownership and unresolved conflicts

- **Fyke:** the four module branches listed in the plan index.
- **Thirdy, per S1:** RBAC, menus, and shared Save/Discard buttons. S3 associates Save/Discard with Fyke's stage-rule work; confirm the split with Sir Roy/Thirdy before implementation. Proposed boundary: Thirdy owns reusable buttons; Fyke owns stage-rule compatibility and testing.
- **TJ, per S1:** territory assignment, stage-specific activity/email templates, and won/lost reasons. Fyke's territory discussion does not transfer implementation ownership.
- Confirm checker/reviewer with the team; do not assume the maker approves their own work.
- Menu/view management and territory implementation are not added to these four modules without an explicit scope decision.

## 2. Mandatory Odoo 20 baseline gate

Complete this before locking a technical design or claiming compatibility:

1. Obtain the exact Odoo 20 edition, build/commit, Python/PostgreSQL requirements, installed CRM/Contacts/HR/web modules, and licensed dependencies for the sample instance.
2. Inspect the actual target models, fields, native category/team/stage functionality, views, conversion flow, and access policies. Candidate names such as `crm.lead`, `crm.stage`, `crm.team`, `res.partner`, `res.users`, and `hr.employee` are inspection targets, not verified APIs in this checkout.
3. Compare native capability against each acceptance case. Reuse a suitable native implementation; extend only the demonstrated gap. Do not create duplicate category concepts merely because this plan suggests a custom model.
4. Verify supported ORM constraints, view modifiers, OWL/web extension points, asset declarations, and test hooks on that exact build. Do not copy old-version `attrs` or patch web internals on assumption.
5. Confirm repository add-on layout, licensing, technical/model names, version convention, and the actual integration branch. Source notes say branch from staging; this checkout has `20` and feature branches but no `staging`. Obtain the agreed base rather than inventing a branch/release policy.
6. Record the findings and decisions in the affected module plan before scaffolding. If Odoo 20 access is unavailable, mark compatibility **blocked/unverified**; do not substitute Odoo 19 and call it Odoo 20 validation.

No baseline instance or API inspection was available during this planning task.

## 3. Architecture and coding standards for future implementation

- **No Odoo Studio.** Deliver installable, reusable, configurable modules; maintain business lookups as records rather than hard-coded selections. Do not embed client names, production IDs, or client-specific stage names.
- Prefer extension by inheritance and supported services over core-file modifications. Keep generic rule/filter mechanisms separate from CRM-specific adapters when the baseline supports a practical split.
- Proposed convention: snake_case fields, PascalCase Python classes, grouped dotted custom models. S1 proposes text `s_`, numeric `n_`, enum `e_`, JSON `j_`, date `d_`, datetime `dt_`, and timestamp `ts_` prefixes.
- Preserve inherited/native field names. For a proposed `s_name`, explicitly configure the supported display-name mechanism (for example `_rec_name`) rather than assuming `name` exists. Boolean/relational prefixes are unspecified; propose conventional `active`, `company_id`, `*_id`, and `*_ids`, then confirm them with the checker.
- Use record-backed Many2one/Many2many relations for categories, teams, fields, roles, and other maintained lookups. Restrict user-selected technical fields/models to an approved allow-list.
- Configuration editing is privileged. Apply ACLs and company-aware record rules to configuration records, with read access only where necessary for authorized runtime behavior. Coordinate company-centric RBAC with Thirdy; do not build a second role system.
- UI hiding, disabled inputs, and dropdown domains are **not security**. Existing ACLs/record rules remain authoritative. Any approved business invariant must be validated server-side for normal UI, quick-create, import, and supported RPC paths.
- Do not use arbitrary Python/JavaScript evaluation, raw SQL, unrestricted `sudo`, or unsafe HTML to implement configurable rules. A typed, validated condition grammar is preferable to executable configuration.
- Keep shared caches keyed by company/user/role/model/view as appropriate. Recheck privileges on configuration retrieval; prevent cross-user/company rule and record leakage.
- Add deterministic ordering, translatable labels/errors, validation of contradictory configurations, and upgrade-safe XML identifiers. Define safe archive/removal behavior instead of cascading away CRM history.

## 4. Proposed schedule and review gates

All dates are in 2026. Confirm timezone, availability, estimates, and feasibility with the team. These are proposed implementation milestones, not work performed by this documentation task.

| Date | Proposed deliverable | Gate |
| --- | --- | --- |
| November 10 | Odoo 20 baseline, scope/ownership decisions, category and team relationship contract | Checker accepts decisions and integration base |
| November 11 | Category model/CRM integration and team mapping foundation | Category contract stable enough for consumer work |
| November 12 | Category/team UI, consistency policy, security and migration checks | Both category modules ready for test pass |
| November 13 | Category and team-category tests, demo evidence, maker/checker review | S1 category deadlines; shared Save/Discard hand-off from Thirdy if available |
| November 16 | Dropdown engine/adapters and reuse demonstration | Confirm HR data access and safe filter policy |
| November 17 | Dropdown regression/evidence/review | S1 dropdown deadline; coordinate TJ's templates contract |
| November 18–20 | Stage-rule engine/CRM adapter, role/condition evaluation, Save/Discard integration | Checker reviews precedence and invalid configurations |
| November 23 | Stage-rule full regression, evidence, certification review | S1 stage-rule deadline |
| November 25 | Align existing browser cases with TJ's standardized Playwright setup | Tooling follow-up, not a reason to defer earlier feature tests |

Two category modules share the November 13 deadline and depend on an unverified baseline. Treat that as a capacity/dependency risk for one developer. Reuse their baseline/design work; escalate a blocked prerequisite or unrealistic date immediately. Do not omit security/tests or silently move source dates. Weekend work is not assumed.

## 5. Verification and certification

For every module plan, turn its acceptance matrix into repeatable fixtures and test results:

1. **ORM/backend:** configuration validation, relations, business invariants, ACLs, company boundaries, active/archive behavior, imports/RPC and upgrade behavior.
2. **Browser:** Playwright is the agreed direction (S1/S4). Cover supported views, unsaved changes, refresh/reopen, roles, errors, keyboard use and the module's negative cases. Record the runner/build actually used; do not claim a repository test harness already exists.
3. **Integration:** test the approved combined modules, then test optional modules absent/disabled. Demonstrate configuration changes without editing source or using Studio.
4. **Lifecycle:** fresh install and module upgrade on a disposable database; rehearse data migration and backup/restore. Do not assume an uninstall or code rollback reverses schema/data changes.
5. **Reuse:** show a second representative configuration/client dataset without code changes. Separate certified module behavior from client-specific configuration UAT. Configuration-only reuse still needs access and integration smoke checks; any code change needs relevant module regression.

Capture exact Odoo build, add-on versions/commits, test command or manual steps, synthetic dataset, role/company, expected/actual outcome, and pass/fail/block status. Performance measurements must state dataset size and an agreed budget; no unmeasured performance claims.

## 6. PR evidence and maker/checker workflow

**Every feature PR must include screenshots or a screen recording that tests the module and its features.** S3 also describes screen-recording proof, so prefer a concise narrated/captioned recording for interactive changes and confirm whether screenshots alone satisfy the checker.

- Map every acceptance-case ID to evidence and test results; cover normal behavior, validation failures, role/company restrictions, persistence, and relevant Save/Discard behavior. Backend test logs supplement, not replace, visible feature evidence.
- Show initial configuration, user action, and visible result. Use captions/timestamps for recordings and enough before/after images for screenshot sequences. Include the tested commit/build so evidence can be reproduced.
- Use synthetic records and redact credentials, deployment keys, customer details, and unrelated private information. Attach through the approved PR mechanism; avoid committing large recordings or private data to Git.
- Maker fills [the PR template](../../.github/pull_request_template.md), runs checks, documents dependencies/migration and asks a checker to reproduce key cases. Checker approval precedes merge.
- This documentation-only work has **no feature-test evidence**. Do not mark feature checklists complete or present plan screenshots as module test proof. When a documentation PR is eventually requested, disclose that no runnable feature exists and have the reviewer determine the applicable evidence; any exception to feature evidence requires explicit reviewer approval.
- Feature PR target must be agreed first: shared version branch versus client staging are different release steps. Keep each module PR scoped to its own module; declare prerequisites instead of mixing sibling work.

## 7. Reuse, deployment, and rollback plan (future work only)

S2 describes reusable module repositories consumed by independent client projects. In this workspace, the four branches are development boundaries, not Git submodules or automatic separate repositories. Confirm final packaging/repository boundaries before publication.

Proposed release procedure, to execute only when authorized:

1. Review/test the reusable module feature branch, merge into the agreed version/default integration branch, and identify an approved immutable commit/tag.
2. In the client repository, add/update the relevant submodule pointer to that exact approved commit. A `.gitmodules` tracking branch does not automatically update the pinned gitlink; submit a separate client change when adopting an update.
3. For a private repository, configure its URL in Odoo.sh settings, add Odoo.sh's generated **public** key as a GitHub deploy key, and rebuild (S2 pp.5–9). Prefer read-only cloning permissions; never store private keys in the repo or PR.
4. Confirm recursive checkout, add-on discovery and manifest dependencies; activate/install or upgrade the module on the sample/staging database. Review Odoo.sh build/test status and run client configuration UAT.
5. Promote the reviewed client commit from staging to production only after checker/UAT approval, a verified backup and an agreed rollout window. No automatic adoption by other clients.
6. Before rollout, record the prior module/submodule commit, schema/data changes and restore procedure. On failure, stop rollout; restore a tested matching database/code pair or apply an approved forward fix. Merely reverting a gitlink is not a safe database downgrade strategy.

None of these deployment or GitHub actions are authorized by the current planning request.
