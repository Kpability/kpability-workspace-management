# Local verification evidence — November 15, 2026

**Not checker certification, client UAT or deployment approval.**
All records and users are synthetic. No company database was accessed.

## Tested code and runtime

- Branch: `feature/dependent-dropdown-filters`; originally `fa14da4`, implementation
  `bd41e2f`, approved default `20` at `cf54708` merged without conflicts in
  `0429dac`. Post-merge tested source: `9bb479d`.
- Current source fingerprint: `8c4051eb9250662eea0cd64b246797b7625c5e4b6915f32977a93c4123019a66`.
  SHA-256 covers 35 sorted relative `.py`, `.xml` and `.csv` paths under the three
  add-ons, each encoded as `path + NUL + file bytes`; excludes docs and caches.
- Runtime-only fingerprint (26 files, excluding `tests`):
  `6f42ab90be825514206fb558ec4dd9bec2e34a4dafdb76a011bcebae82fb0463`.
  No runtime implementation changed during integration or additional Brave
  verification; only tests/docs changed. The preceding actual-Brave source
  fingerprint was `70d83258b99827e605bc3e5d77c71599bee09af8f993704d4245d28f9d183fce`.
  The earlier model regression and five-case bundled-browser run used fingerprint
  `fa1d9dda312a76929676d9099bab36815fccb5e46d6f127df4bc336fc8ff47c3`.
- Odoo: `20.0+e`; Community `24f007f4f8a2dbdab05c1b4aecf48bd4e9c4251e`,
  Enterprise `7773cfc038583d1b664491128424cd1904be946c`.
- CPython 3.12.14; PostgreSQL 16; Playwright 1.65.0.
- Latest browser: **actual Brave through remote-debugging CDP**, engine
  `156.0.8078.80`; `navigator.brave.isBrave()` returned `true`.
  This is distinct from the earlier bundled Chromium `158.0.8127.18`.
- Effective application viewport: 1440 × 1000 CSS pixels. Brave's inherited 140%
  site zoom was preserved; only owned test-page geometry was adjusted. This is
  desktop evidence, not mobile or comprehensive zoom/accessibility certification.
- Full browser database: owned disposable `kpability_ddf_enterprise`,
  HTTP `127.0.0.1:18043`, database `127.0.0.1:55427`.

## Passing post-merge actual-Brave remote-debugging run

`/tmp/opencode/kpability-ddf-browser/20261115152849/`

The [copied results manifest](browser-results.json) records **10 passed, 0 failed**, `transport=remote-debugging-cdp`,
`brave_verified=true`, no page JavaScript or console errors, and per-case
screenshots/video filenames. The suite completed in 28.997 seconds; that is
test duration, not a product performance benchmark. The user explicitly authorized
PR screenshots. Curated synthetic PNGs are committed beside this index; original
case screenshots/video filenames in the manifest refer to the retained local run.
Raw videos, credentials, session logs and reference PDFs are not committed.

The existing Brave browser was attached after the user's remote-debugging
approval. Tests used new owned browser contexts against the synthetic database;
existing personal/company tabs and browser profile settings were not inspected
or changed. Cleanup closes only owned contexts and disconnects, not Brave.

| Case / acceptance | Action and verified result | Committed synthetic screenshot |
| --- | --- | --- |
| `test_00`, DDF-01 | Administrator opens maintained CRM salesperson rule; tenant, supported binding, Active and exact configured department are visible | [Configuration](DDF01-maintained-configuration.png) |
| `test_01`, DDF-02 | Both native opportunity and lead Contact autocomplete/Search More include 12 eligible direct contacts and exclude other-company/archived contacts | [Opportunity](DDF02-opportunity-search-more.png), [lead](DDF02-lead-search-more.png) |
| `test_02`, DDF-05–06 | Edit name and parent without losing old child/draft; warning; explicit valid reselection; native Save completes; persisted RPC read confirms; native Discard restores saved relationship | [Stale draft retained](DDF05-stale-draft-preserved.png); full sequence in local video |
| `test_03`, DDF-03/10 | Company Contacts Primary Contact reuses filter; other-company option and creation shortcut absent | [Contacts reuse](test_03_contacts_reuse_and_no_creation_shortcut.png) |
| `test_04`, DDF-07/09 | Ordinary salesperson sees eligible public-HR-mapped user only; private HR field read/config writes denied; invalid assignment and parent-only RPC writes rejected | [Ordinary salesperson](DDF07-sales-user-public-HR.png) |
| `test_05`, DDF-04 | Missing parent and a saved company without children both return an empty native picker response, never unrestricted choices | [Missing parent](DDF04-missing-parent.png), [empty company](DDF04-empty-company.png) |
| `test_06`, DDF-01/08 | Administrator changes the maintained department in native configuration UI and saves; reopening the lead changes eligible users without code or rewriting its existing assignment | [Configuration change](DDF08-configuration-change-no-backfill.png) |
| `test_07`, DDF-11 | RPC deactivation restores native contact choices; reactivation preserves the now-stale value and permits an unrelated legacy edit | [Native choices restored](DDF11-inactive-native-choices.png) |
| `test_08`, DDF-05/10 | ArrowDown/ArrowUp/Enter selects an eligible contact through the native widget; Discard restores the saved contact | [Keyboard selection](DDF10-keyboard-selection.png) |
| `test_09`, DDF-05 | Hold older parent-B onchange while selecting A, then release B; final native autocomplete request domain, response IDs and visible options all match the latest parent A | [Older request pending](DDF05-new-parent-old-request-pending.png), [latest parent wins](DDF05-latest-parent-filter.png) |

For `test_04`, use the **second** video in its `results.json` entry: it is the
ordinary-user browser context. The first context remains an unused admin page.
Its case-level `effective_viewport` describes that unused `about:blank` page
(2016 × 1400); use the actual ordinary-user `DDF07` capture (1440 × 1000), not
that blank page, for UI review.
Backend denials are asserted from structured RPC responses; the screenshot alone
does not prove those denials.

Network diagnostics are retained: four cases include `net::ERR_ABORTED` for
`/bus/websocket_worker_bundle` during test-page navigation. These are not reported
as successful requests or suppressed. Dropdown RPC assertions and all ten cases
passed; there were no JavaScript/console errors.

The earlier **10/10 actual-Brave** run remains at
`/tmp/opencode/kpability-ddf-browser/20261115145926/`; the new passing run above
repeats those checks after the approved default-branch merge.
The earlier **5/5 bundled Chromium** run remains at
`/tmp/opencode/kpability-ddf-browser/20261115142914/`. It was not Brave testing and
is not used as a substitute for the CDP evidence above.

Earlier failed runs remain in the parent evidence directory. They are not the
passing evidence set. Browser-run fixes addressed native selectors, fixture keys
and waiting for native Save/onchange response bodies and OWL rendering; no native
save or onchange semantics were replaced. The controlled race is one reproducible
ordering, not exhaustive concurrency coverage.

## Model tests and lifecycle

| Evidence | Result |
| --- | --- |
| `/tmp/opencode/kpability-ddf-postmerge-upgrade-final.log` | **80 authored pass**: 30 dropdown + 43 approved pipeline-category + 7 website checks; zero failures/errors |
| `/tmp/opencode/kpability-ddf-postmerge-fresh-final.log` | **82 pass**: same 80 authored checks plus 2 framework cases; zero failures/errors; fresh `kpability_ddf_combined_final` |
| `/tmp/opencode/kpability-ddf-postmerge-lifecycle-check.log` | Post-merge same-version upgrade preserves original exact assignments/audit fields; zero rules, blank new business fields |
| `/tmp/opencode/kpability-ddf-lifecycle.json` | Original `before`, `after_install`, `after_upgrade` plus post-merge `after_upgrade` all preserved |
| `/tmp/opencode/kpability-ddf-core.log` | Earlier core-only fresh install; 7 authored checks, 9 including framework; zero failures/errors |
| `/tmp/opencode/kpability-ddf-contacts-2.log` | Earlier CRM/Contacts without HR; 19 authored checks; zero failures/errors |
| `/tmp/opencode/kpability-ddf-enterprise.log`, `/tmp/opencode/kpability-ddf-final-tests-2.log` | Earlier full install/upgrade; 27 authored checks before the three optional integration tests; zero failures/errors |

The final regression includes an unrelated Contacts VAT-edit case: native
company classification may change without revalidating an unchanged legacy
salesperson. Company/contact relationship changes remain validated normally.
The three post-merge optional tests verify category/contact repair and preservation,
unchanged legacy contact edits during category assignment, and eligible
department assignment alongside native categorized Won/lost behavior. No runtime
code was changed to accommodate the approved pipeline modules. A compact
[validation summary](postmerge-validation.json) records source and result counts.

Python/XML syntax and whitespace validation passed for the 35 source files
(34 Python/XML plus the Odoo 20 access CSV). `git diff --check` passed.

## Reproduce / review

See the [implementation record](../dependent-dropdown-filters.md) for commands,
guards, source traceability, acceptance gaps and activation/release gates.
The browser server is stopped after verification; synthetic databases and
artifacts are retained locally for review. Credentials remain in the separate
mode-`0600` fixture file, not this index or Git. Do not publish credential files,
raw session-bearing logs or unrelated data.

Outstanding: independent checker/HR-owner approval, integration with unmerged
team/stage/shared-button work, external/portal integration review, realistic performance budgets,
wider concurrency/keyboard/mobile/accessibility cases, Odoo.sh/UAT and
backup/restore. The implementation record maps DDF-01–12 to local proof and
remaining gates; passing this suite is not an assertion that every standard is
certified.
