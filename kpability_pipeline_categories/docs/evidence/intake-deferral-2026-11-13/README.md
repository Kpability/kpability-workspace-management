# Website/email deferral: current evidence

Follow-up to merged [PR #4](https://github.com/Kpability/kpability-workspace-management/pull/4).
Future website/email integration remains tracked in [issue #6](https://github.com/Kpability/kpability-workspace-management/issues/6).

| Screenshot | What it shows |
| --- | --- |
| [Core category configuration](category-without-intake-tabs.png) | Stage configuration remains; Incoming Email Addresses and Websites tabs are absent. |
| [Scoped CRM pipeline](scoped-crm-pipeline.png) | The category's mapped columns and opportunity remain available after reload. |

Original, unedited **1440×1000** browser captures from November 13, 2026.
All records are synthetic; no client data or credentials are included.

- Runtime: **Odoo 20.0+e**, Python 3.12.14, PostgreSQL 16.15.
- Server: `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`.
- Enterprise: `7773cfc038583d1b664491128424cd1904be946c`.
- Core `20.0.1.2.0`; retired compatibility module `20.0.1.1.0`.
- Playwright 1.65.0; Chromium 158.0.8127.18.
- Disposable local database: `kpability_pipeline_defer_fresh`, port 18027.
- Run `1113013907`: **12 browser checks passed** in **17.975s**.
- Fixture category IDs 36/37, stage IDs 23–26, opportunity IDs 191/192;
  additional draft/quick-create records are expected.

Sources in `/tmp/opencode/kpability-pipeline-e2e/1113013907/`:
`test_11_category_has_no_website_or_email_configuration.png` and
`test_02_scoped_board_columns_and_reload.png`. Copies were verified byte-for-byte.

Separate Odoo checks passed: **45 core tests**, **53 combined tests**, a fresh
core-only Enterprise install, and a real versioned upgrade preserving existing
CRM records/configuration while retiring only owned pipeline aliases.
See [full results](../../pipeline-categories.md#7-current-deferral-verification-november-13-2026).
This is local verification, not an Odoo.sh deployment or independent approval.
