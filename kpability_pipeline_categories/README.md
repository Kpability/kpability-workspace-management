# Kpability Pipeline Categories

Reusable category records and category-aware CRM stages for **Odoo 20 Enterprise**.
The add-on depends on native `crm`; Enterprise validation uses `web_enterprise`
and `crm_enterprise` installed alongside it. No Studio, custom role system, or
frontend patch is required.

## Install and configure

1. Include this repository root in the server's add-on path, alongside the
   matching Odoo 20 server and Enterprise add-ons.
2. Install `kpability_pipeline_categories`.
3. As a Sales Manager, open **CRM → Configuration → Pipeline → Pipeline Categories**.
   The **Sales → Pipeline Categories** entry also lets sales users browse categories.
4. Create a category and select existing CRM stages. Leave **Company** empty for a
   shared category, or select its owning company. Include a compatible **Won**
   stage if the native Won action is needed.
5. Save, then select **Open Pipeline**. The category's board limits its records
   and stage columns and supplies the category when creating a card.

Stage order is native/global, not separately configurable per category. A stage
can belong to several categories. Native stage/sales-team restrictions still
apply. Manage mappings on the category; their inverse on stages is read-only.

## Record behavior

- A lead/opportunity has at most one category. It is optional: existing records
  are not backfilled, and uncategorized CRM behavior remains native.
- A category with no mapped stage does **not** mean every stage is available.
- The main CRM pipeline remains a mixed-category overview. Ordinary search
  filters restrict records, not category-specific empty columns; use
  **Open Pipeline** for the scoped board.
- Category changes do not silently replace an existing stage. Choose a
  compatible stage explicitly, or clear the category, before saving.
- Shared categories apply across companies without granting access to their
  opportunities. Company-specific categories require a matching record company;
  companyless records can only use shared categories.
- Sales users can read permitted categories. Native Sales Managers configure
  them, including shared configuration with cross-company effect.
- Archived categories remain readable on existing records but cannot be newly
  assigned. Unrelated edits to those records remain possible.
- Names are Unicode-normalized, whitespace-normalized and case-insensitive for
  uniqueness within each company/shared scope. Archived names remain reserved.
- Used categories cannot be deleted. Removing a used mapping or narrowing its
  company/team scope is blocked even for archived or otherwise hidden records.
  Explicitly reclassify affected records before changing configuration. Errors
  do not disclose hidden records.
- Native Won/Lost is retained. Bulk Won chooses an eligible Won stage for each
  category/team; a missing compatible Won stage blocks the action. Merge requires
  matching classification, including categorized versus uncategorized records.

## Consumer contract

The standalone model is `crm.pipeline.category`; CRM classification is
`crm.lead.pipeline_category_id`. Mappings are `category.stage_ids`, with
`crm.stage.pipeline_category_ids` as a read-only inverse.

`category._check_assignable()` is the common read-access/active-category check.
Optional consumers must further narrow eligibility without broadening native
stage or record access. The base add-on does not depend on team/category mapping,
stage rules, dropdown engines, reason dialogs or `workspace_management`.

## Validation and release

Run the Odoo transaction suite with:

```bash
python /path/to/odoo/odoo-bin \
  --addons-path=/path/to/enterprise,/path/to/odoo/addons,/path/to/this/repository \
  --database=your_disposable_test_database \
  --update=kpability_pipeline_categories \
  --test-enable --test-tags=/kpability_pipeline_categories --stop-after-init
```

Supply database connection settings separately. Fresh-install validation must
also install `web_enterprise,crm_enterprise` to exercise the intended edition.
See [implementation and verification](docs/pipeline-categories.md)
for the actual tested revisions, results, local setup and outstanding checks.
Module-specific documentation and screenshots live in `docs/`; both the Odoo
suite and the standalone browser runner live in `tests/`.

Do not infer categories from historical names or overwrite legacy data. Take a
matching database/filestore/code backup before rollout; rollback is not merely a
code checkout. Odoo.sh integration, optional-module regression and independent
checker approval are separate release gates; local success is not production
certification.
