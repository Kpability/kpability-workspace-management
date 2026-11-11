# Six-case browser walkthrough

**Result: 6 passed, 0 failed.** Executed November 11, 2026, at 09:40 UTC on local
**Odoo 20 Enterprise (`20.0+e`)**, database `kpability_pipeline_dev`.

| Test | Browser action | Actual result | Screenshot |
| --- | --- | --- | --- |
| 1. Create category | CRM → Configuration → Pipeline Categories → New; select New, Qualified and Won; Save | Category saved with exactly those mappings | [View](01-passed.png) |
| 2. Open pipeline/create opportunity | Category → Open Pipeline → New; create Test Deal | Only three mapped columns; category assigned automatically; persisted after refresh | [View](02-passed.png) |
| 3. Valid move | Drag the deal from New to Qualified; refresh | Stage changed and remained Qualified | [View](03-passed.png) |
| 4. Invalid move | Main CRM pipeline; drag Qualified → Proposition | Expected validation dialog; persisted stage remained Qualified | [View](04-passed.png) |
| 5. Save/Discard | Edit revenue; Discard; edit again; Save and refresh | Discard restored 0; Save retained 4,321 | [Discard](05a-discard-restored-original.png) / [Save](05-passed.png) |
| 6. Won | Open the deal; click Won; refresh | Mapped Won stage, 100% probability, category preserved | [View](06-passed.png) |

**The validation error in test 4 is expected protection, not a failed test.**
Screenshots are original 1440×1000 browser captures, not generated mockups.

Synthetic records retained for inspection:
- [Test Pipeline 094008](http://127.0.0.1:18020/odoo/crm.pipeline.category/29)
- [Test Deal 094008](http://127.0.0.1:18020/odoo/crm.lead/116), now Won

The six steps were executed with browser automation; direct RPC calls verified
saved values without changing data. No application code, existing stages, client
data or Odoo.sh environment was changed. This is not independent checker sign-off.

[Machine-readable results](results.json). Run: `20261111T094008Z`, Chromium
`158.0.8127.18`. Raw captures and the local runner remain under
`/tmp/opencode/kpability-pipeline-manual/`. See the [earlier evidence](../README.md)
for the separate eight-test regression suite.
