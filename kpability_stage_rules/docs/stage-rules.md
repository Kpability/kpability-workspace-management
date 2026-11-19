# CRM opportunity stage rules

## Behavior and scope

- Supported fields: Expected Closing, Salesperson, Campaign, Medium, Source, and Referred By. Conditions can also use Priority. One condition per rule is shared by all of its conditional options.
- Sales and marketing relations support **Is set** / **Is not set**. Referred By also supports case-sensitive equality (outer spaces are ignored). Expected Closing also supports equality and before/after a fixed date. Priority uses the native CRM choices. No free-form expressions or relationship traversal are evaluated.
- A rule applies to the opportunity's company and stage, optionally narrowed to an existing Odoo group (including implied membership). Shared opportunities with no company do not match. Rules are inactive by default and refreshed when the opportunity form is reopened. Only CRM administrators can manage configuration, within Odoo's enabled-company scope.
- **Use Odoo default** leaves the native behavior alone. Matching rules can only add restrictions. If multiple rules match, hide or read-only wins over inherited settings, and any requirement applies. An obvious contradiction within one rule is rejected. If overlapping rules leave an empty required field hidden or read-only, the form keeps the draft and explains what must change.
- Moving from or to a configured stage in the opportunity form previews the change. Explicit **Save** commits it, and **Discard** restores the saved stage and values. Until then, actions such as Won cannot silently save the pending transition. Stages with no applicable rules use Odoo's normal behavior. Stage rules do not change the existing Won action or its optional reason wizard.
- Existing values are not changed on install, activation, or when a rule hides a field. Salespeople can save an edit made while a field was editable even if a later draft change locks it. Server access checks and native modifiers still apply. Stage rules are not authorization or server validation; the kanban, quick creation, imports, automations, and RPC writes are outside scope.

## Implementation

- `stage.rules` stores typed, allow-listed rules. `crm.lead.get_stage_rules_for_form()` exposes presentation settings filtered by enabled company, effective groups, and readable CRM fields. Because matching runs in the browser, do not enter confidential information as comparison values. There is no per-field privileged record read.
- An inherited CRM view selects a CRM-specific form controller, parser, and record model. The evaluator consumes live draft values. It composes fixed modifiers with native labels and field widgets and preserves the CRM form's existing synchronization and stage effects. No generic web-client patch or Studio record is installed.
- Custom fields follow the [shared naming standards](../../docs/development/shared-standards.md): `s_` for text, `e_` for selections, `j_` for JSON, and `d_` for dates. Native fields, group membership, and relation names are preserved.
- Archive a rule to stop applying it without deleting it. At most one active rule exists per company, stage, field, and exact audience. Uninstall removes configuration and restores the default CRM form; it does not migrate or undo opportunity data.

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
