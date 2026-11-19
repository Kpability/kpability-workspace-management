# Stage Rules verification evidence

Screenshots are from a passing local Odoo 20 Enterprise run in Brave (Chromium `156.0.8078.80`) via Playwright `1.65.0` over remote debugging. All records shown are synthetic. Both editions passed the same five browser scenarios; Community ran without the optional Pipeline Categories and Won Reasons modules. See the [verification guide](../stage-rules.md#verification) for the exact Odoo builds and commands.

| Case | Passed checks | Screenshots |
| --- | --- | --- |
| SR-01 · Rule configuration | The native editor offers operators valid for the selected condition field and saves the rule inactive. | [Rule editor](05-native-stage-rule-editor.png) |
| SR-02 · Stage preview, Save and Discard | Clicking Qualification previews rules without writing. A missing Expected Closing blocks Save. Discard restores Intake and its visibility rules. A valid date and stage persist together and the stage is still selected after reload. | [Blocked Save](01-required-date-keeps-stage-in-draft.png) · [Discard](01b-discard-restores-original-stage.png) · [Saved stage and date](02-stage-and-date-saved.png) |
| SR-03 · Conditions and audiences | Campaign shows Referred By for the salesperson as the draft changes. The manager-only restriction does not lock the salesperson's Campaign. When the referral later becomes read-only, the value entered earlier still saves. | [Visible referral](04a-conditional-visibility-for-salesperson.png) · [Read-only draft retained](04-conditional-readonly-preserves-draft.png) |
| SR-04 · Conflicting rules | An empty field made both hidden and required produces a warning; neither the draft nor saved record is overwritten. | [Conflict warning](07-conflicting-rules-explain-why-save-is-blocked.png) |
| SR-05 · Native compatibility | An unconfigured stage retains native autosave before Lost. With merged Pipeline Categories and Won Reasons installed, submitting the Won wizard saves the selected reason, moves to the mapped Won stage, and preserves Expected Closing. | [Unconfigured form](06-unconfigured-stage-is-native.png) · [Won reason selected](03-merged-won-reasons-wizard.png) |

**Model tests:** 6/6 Stage Rules cases passed on a fresh standalone Community install (plus 2 framework tests) and 6/6 on the combined Enterprise upgrade. Cases cover typed rule validation, inactive configuration, duplicates, company and effective group scoping, manager-only configuration, and unchanged direct opportunity writes.

**Release status:** Independent review and client staging/UAT have not run. No production action was taken.
