## Summary and scope

- Module:
- Feature branch:
- Agreed target branch:
- Change type: documentation / configuration / implementation / migration
- Development plan and requirement/case IDs:
- User-visible outcome:
- Explicitly out of scope:

## Dependencies and design decisions

- Required module versions / prerequisite PRs:
- Approved decisions and remaining questions:
- Native Odoo capability reused; customization needed:
- Studio usage: none

## Test environment

- Odoo 20 edition and exact build/commit:
- Add-on versions and tested commit:
- Database / synthetic dataset:
- Browser and test runner versions:
- Roles and companies tested:

## Testing results

Do not mark a planned test as passed. State pass, fail, blocked, or not run with a reason.

| Case ID | Steps or automated command | Expected result | Actual result / status | Evidence link or timestamp |
| --- | --- | --- | --- | --- |
| Enter the plan's case ID | Enter reproducible steps | Enter expectation | Enter observed result | Attach evidence |

## Required screenshots or screen recording

**Feature PRs must include screenshots or a screen recording demonstrating tests of the module and its features.** Prefer a recording for interactive behavior and confirm any stricter checker requirement.

- Attachments/links, captions and recording timestamps:
- Configuration/setup demonstrated:
- Positive and negative cases demonstrated:
- Roles/company isolation demonstrated:
- Save/Discard and reopen/persistence demonstrated where applicable:
- Backend test logs (supplementary, not a replacement for visual evidence):

Documentation-only changes: explicitly state that no feature was implemented/tested, leave feature checks incomplete, and obtain reviewer agreement on evidence applicability. Never substitute a document screenshot for proof that a module works.

## Security, lifecycle, and compatibility

- ACLs/record rules and configuration permissions checked:
- UI behavior versus backend business/security enforcement:
- Company boundaries and configuration/cache isolation:
- Fresh-install and upgrade results:
- Existing-record migration and archive/deletion behavior:
- Optional modules absent and combined-module regression results:
- Known limitations / performance dataset and measurements:

## Release and rollback (if applicable)

- Reusable module release commit/tag:
- Client submodule old/new commit and separate adoption PR:
- Sample/staging build and UAT result:
- Backup, migration, rollback/restore or forward-fix procedure:
- Production action requested (none unless explicitly approved):

## Maker/checker review

- Maker:
- Checker:
- Cases reproduced by checker and result:
- Unresolved blockers / approved deferrals:

### Feature readiness checklist

- [ ] One module per feature branch; prerequisites declared.
- [ ] Odoo 20 build and native capability baseline verified.
- [ ] No Studio, secrets, private deployment keys, or real customer data included.
- [ ] All acceptance cases have actual results; failures/blockers disclosed.
- [ ] Screenshots or recording test the module and its features, linked by case ID.
- [ ] Backend security, company isolation, upgrade and integration checks completed.
- [ ] Configuration/reuse instructions and migration/rollback notes updated.
- [ ] Checker reproduced key tests and approved the change.
