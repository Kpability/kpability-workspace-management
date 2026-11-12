# Kpability Website Pipeline Categories

Optional website companion for
[`kpability_pipeline_categories`](../kpability_pipeline_categories/README.md).

## What it does

- Lets a website visitor choose one or more **pipeline categories** in a CRM form.
- Creates **one CRM opportunity per selected pipeline**, never two in the same
  pipeline for one submission.
- Shows only active, stage-configured categories explicitly enabled on the current
  website and compatible with the website company.
- Preserves native `website_crm` behavior: visitor/partner identity, phone
  normalization, website company, language, description, attachments and UTM
  handling.

Incoming-email routing is part of the base add-on: each pipeline can own one or
more native email aliases, and duplicate routes into the same pipeline are
suppressed for a single message.

## Installation

1. Install `kpability_pipeline_categories` and `website_crm`.
2. Install `kpability_website_pipeline_categories`.
3. Open **CRM → Configuration → Pipeline → Pipeline Categories**.
4. On each pipeline, open the **Websites** tab and select the websites where it
   may be offered.

## Adding the form

In the website editor, open the block picker and add **CRM Pipeline Form** under
**Contact & Forms**. It includes name, email, company, phone, message and a
pipeline selector populated from the server. The selector supports choosing
multiple pipelines.

The public endpoint is `GET /kpability/pipeline-categories`. The form posts to the
standard `/website/form/crm.lead` route; category selections are validated again
on the server, and an unavailable or archived category rejects the whole request
instead of creating a partial set of opportunities.

## Security

- Website visitors do not receive category read access.
- The public endpoint exposes only the display name and description of categories
  enabled for that website.
- All availability and company checks are repeated in `insert_record()`; the
  browser selection is not trusted.

## Tests

```bash
--test-tags=/kpability_website_pipeline_categories
```

The test module covers availability, the public endpoint, native form submission
configuration, two-pipeline creation, duplicate selections, unavailable-category
rollback, and attachment contents in every created record. The base add-on's
optional Playwright case also submits the actual public form, verifies the
success redirect and checks both persisted opportunities. Staging website UAT
and external email delivery still require access and gateway configuration.
