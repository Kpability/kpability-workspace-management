# Website Pipeline Categories — retired compatibility module

Website and incoming-email intake are deferred to a separate reviewed PR:
[issue #6](https://github.com/Kpability/kpability-workspace-management/issues/6),
following merged [PR #4](https://github.com/Kpability/kpability-workspace-management/pull/4).

**Do not install this module on new deployments.** Install only
[`kpability_pipeline_categories`](../kpability_pipeline_categories/README.md)
for core CRM pipeline categories.

## Existing installations

Keep this directory available and upgrade both installed Kpability modules.
Removing an installed add-on or uninstalling it is not a safe substitute for
this upgrade. Back up the database, filestore and matching code first.

This module now retains only upgrade compatibility:

- Existing `website_ids` mappings remain stored, without an exposed configuration tab.
- The editor snippet is inactive and the public category endpoint is removed.
- Existing `t-call` references resolve to an unavailable notice, not a form.
- Previously copied pipeline forms are disabled by a small browser guard.
- Cached pipeline-selection submissions are rejected; no fan-out or custom
  attachment handling remains.
- Ordinary native `website_crm` submissions are untouched.

Existing website pages, CRM records and mappings are not deleted. The base
module separately retires its owned email aliases while retaining their
configuration. Re-enabling either integration requires the future reviewed PR.

## Regression checks

Use `--test-tags=/kpability_website_pipeline_categories` on an isolated Odoo 20
Enterprise database. Tests cover the retired endpoint, rejected stale submissions,
retained mappings/template references, inactive UI, and ordinary native CRM forms.
