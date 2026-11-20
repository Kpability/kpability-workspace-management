# CRM opportunity stage rules

## Behavior and scope

- Expected Closing, Salesperson, Campaign, Medium, Source, and Referred By are pre-registered. Use **Create and edit…** from the **Opportunity Fields** dropdown to register another standard or custom field already on the CRM opportunity form. Registration does not change the CRM model or form. Supported types are checkbox, short/long text, date/date-time, whole/decimal/monetary numbers, selection, Many2one and Many2many. Stage, company, record ID, and lead/opportunity type are not targets.
- Visibility, Editing, and Requirement each have their own native Odoo condition builder. Conditions can combine multiple clauses with **all/any** and offer operators and values appropriate to each field type. They use values in the open form, including unsaved edits. Visibility and Editing cannot depend on fields controlled by the same rule because that can make a condition impossible for a salesperson to satisfy. Dotted relationship paths, hierarchy tests, and expressions such as relative dates are not available.
- A rule applies to the opportunity's company and any selected stage, and to users in **any** selected group, including implied membership. No groups means everyone in that company. Shared opportunities with no company do not match. Rules are inactive by default and refreshed when the opportunity form is reopened. Only CRM administrators can manage configuration, within Odoo's enabled-company scope.
- **Use Odoo default** leaves the native behavior alone. Matching rules can only add restrictions. If multiple rules match, hide or read-only wins over inherited settings, and any requirement applies. A rule cannot always hide or lock a field it also requires. If overlapping rules or native modifiers leave a required field hidden or read-only and empty, Save keeps the draft and explains the conflict. This includes native required fields that a stage rule would otherwise hide.
- Moving from or to a configured stage in the opportunity form previews the change. Explicit **Save** commits it, and **Discard** restores the saved stage and values. Until then, actions such as Won cannot silently save the pending transition. Stages with no applicable rules use Odoo's normal behavior. Stage rules do not change the existing Won action or its optional reason wizard.
- Existing values are not changed on install, activation, or when a rule hides a field. Salespeople can save an edit made while a field was editable even if a later draft change locks it. Server access checks and native modifiers still apply. Stage rules are not authorization or server validation; the kanban, quick creation, imports, automations, and RPC writes are outside scope.

## Implementation

- `stage.rules.field` registers technical field names from the effective opportunity form. `stage.rules` stores separate domains validated against literal operands and supported field types. `crm.lead.get_stage_rules_for_form()` exposes presentation settings filtered by enabled company, effective groups, and readable CRM fields. Conditions that depend on fields absent from the user's open form are skipped; they are not evaluated against empty values. Because matching runs in the browser, do not enter confidential information as comparison values. There is no per-field privileged record read.
- An inherited CRM view selects a CRM-specific form controller, parser, and record model. The evaluator consumes live draft values. It composes fixed modifiers with native labels and field widgets and preserves the CRM form's existing synchronization and stage effects. No generic web-client patch or Studio record is installed.
- Custom configuration follows the [shared naming standards](../../docs/development/shared-standards.md): `s_` for text, `e_` for selections and `j_` for JSON. Native CRM fields and Odoo group membership are preserved.
- Archive a rule to stop applying it without deleting it. Upgrading from `20.0.1.0.0` retains existing rules: the previous stage, field and group become tags and the shared condition is copied into each conditional behavior. Uninstall removes Stage Rules configuration and restores the default CRM form; it does not remove registered CRM fields from the CRM model or undo opportunity data.

## Verification

Local baseline: Odoo `20.0` core `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`, Enterprise `20.0+e` with `7773cfc038583d1b664491128424cd1904be946c`, Python 3.12.14, PostgreSQL 16.15, and Playwright 1.65.0 over local Brave/Chromium CDP (Chromium 156.0.8078.80). The integration checkout was based on `origin/20` at `c670310`. Independent review and client staging are still pending.

On a disposable local PostgreSQL 16+ database, use the same `--addons-path` and connection settings as the normal Odoo instance. Install the add-on with `-i kpability_stage_rules --without-demo=True`, or upgrade an installed copy with `-u kpability_stage_rules`. Add `--test-tags=/kpability_stage_rules --stop-after-init` to run the ORM suite. To test optional integration on Enterprise, also install `crm_enterprise`, `kpability_pipeline_categories`, and `crm_stage_reasons`.

Run the browser tests with Python Playwright 1.65.0 and its Chromium, or point `ODOO_E2E_CDP_URL` to an isolated loopback Chromium/Brave CDP session. The script writes synthetic data; use a disposable local database with `kpability_stage_rules_` in the name and set `ODOO_E2E_PASSWORD` via the environment.

```sh
ODOO_E2E_ALLOW_WRITES=1 \
ODOO_E2E_DATABASE=kpability_stage_rules_review \
ODOO_E2E_URL=http://127.0.0.1:18031 \
python kpability_stage_rules/tests/e2e/test_stage_rules.py -v
```

New screenshots are written under `/tmp/opencode/kpability-stage-rules-browser/<run_id>/` by default. See [test results and screenshots](evidence/README.md) for the captured Enterprise run and case IDs. No test fixtures are installed in client databases.
