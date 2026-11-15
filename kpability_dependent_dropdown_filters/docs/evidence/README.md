# Local verification evidence — November 15, 2026

**Not checker certification, client UAT or deployment approval.**
All records and users are synthetic. No company database was accessed.

## Tested code and runtime

- Branch: `feature/dependent-dropdown-filters`, parent `fa14da4`; changes uncommitted.
- Current source fingerprint: `70d83258b99827e605bc3e5d77c71599bee09af8f993704d4245d28f9d183fce`.
  SHA-256 covers 35 sorted relative `.py`, `.xml` and `.csv` paths under the three
  add-ons, each encoded as `path + NUL + file bytes`; excludes docs and caches.
- Runtime-only fingerprint (26 files, excluding `tests`):
  `6f42ab90be825514206fb558ec4dd9bec2e34a4dafdb76a011bcebae82fb0463`.
  No runtime implementation changed during the additional Brave verification;
  changes were limited to the browser runner and documentation. The earlier model
  regression and five-case bundled-browser run used whole-source fingerprint
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

## Passing actual-Brave remote-debugging run

`/tmp/opencode/kpability-ddf-browser/20261115145926/`

`results.json` records **10 passed, 0 failed**, `transport=remote-debugging-cdp`,
`brave_verified=true`, no page JavaScript or console errors, and per-case
screenshots/video filenames. The suite completed in 26.224 seconds; that is
test duration, not a product performance benchmark. Artifacts are kept outside Git; attach
curated screenshots or a captioned recording through the approved PR mechanism
only when publication is authorized.

The existing Brave browser was attached after the user's remote-debugging
approval. Tests used new owned browser contexts against the synthetic database;
existing personal/company tabs and browser profile settings were not inspected
or changed. Cleanup closes only owned contexts and disconnects, not Brave.

| Case / acceptance | Action and verified result | Named screenshot in run directory |
| --- | --- | --- |
| `test_00`, DDF-01 | Administrator opens maintained CRM salesperson rule; tenant, supported binding, Active and exact configured department are visible | `DDF01-maintained-configuration.png` |
| `test_01`, DDF-02 | Both native opportunity and lead Contact autocomplete/Search More include 12 eligible direct contacts and exclude other-company/archived contacts | `DDF02-opportunity-search-more.png`, `DDF02-lead-search-more.png` |
| `test_02`, DDF-05–06 | Edit name and parent without losing old child/draft; warning; explicit valid reselection; native Save completes; persisted RPC read confirms; native Discard restores saved relationship | `DDF05-stale-draft-preserved.png`; full sequence in case video |
| `test_03`, DDF-03/10 | Company Contacts Primary Contact reuses filter; other-company option and creation shortcut absent | `test_03_contacts_reuse_and_no_creation_shortcut.png` |
| `test_04`, DDF-07/09 | Ordinary salesperson sees eligible public-HR-mapped user only; private HR field read/config writes denied; invalid assignment and parent-only RPC writes rejected | `DDF07-sales-user-public-HR.png` |
| `test_05`, DDF-04 | Missing parent and a saved company without children both return an empty native picker response, never unrestricted choices | `DDF04-missing-parent.png`, `DDF04-empty-company.png` |
| `test_06`, DDF-01/08 | Administrator changes the maintained department in native configuration UI and saves; reopening the lead changes eligible users without code or rewriting its existing assignment | `DDF08-configuration-change-no-backfill.png` |
| `test_07`, DDF-11 | Deactivation restores native contact choices; reactivation preserves the now-stale value and allows an unrelated legacy edit without rewriting history | `test_07_deactivation_restores_native_choices_without_rewriting_history.png` |
| `test_08`, DDF-05/10 | ArrowDown/ArrowUp/Enter selects an eligible contact through the native widget; Discard restores the saved contact | `DDF10-keyboard-selection.png` |
| `test_09`, DDF-05 | Hold older parent-B onchange while selecting A, then release B; final native autocomplete request domain, response IDs and visible options all match the latest parent A | `DDF05-latest-parent-filter.png`; controlled sequence in case video |

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
| `/tmp/opencode/kpability-ddf-core.log` | Core-only fresh install; 7 authored checks, 9 including framework; zero failures/errors |
| `/tmp/opencode/kpability-ddf-contacts-2.log` | CRM/Contacts without HR; 19 authored checks; zero failures/errors |
| `/tmp/opencode/kpability-ddf-enterprise.log` | Full fresh Enterprise install; 27 authored checks, 29 including framework; zero failures/errors |
| `/tmp/opencode/kpability-ddf-final-tests-2.log` | Final full upgrade regression; 27 authored checks; zero failures/errors |
| `/tmp/opencode/kpability-ddf-lifecycle.json` | `before`, `after_install`, `after_upgrade` all preserved; exact native assignments and create/write audit values unchanged; zero seeded rules and blank added business fields |

The final regression includes an unrelated Contacts VAT-edit case: native
company classification may change without revalidating an unchanged legacy
salesperson. Company/contact relationship changes remain validated normally.

Python/XML syntax and whitespace validation passed for the 35 source files
(34 Python/XML plus the Odoo 20 access CSV). `git diff --check` passed.

## Reproduce / review

See the [implementation record](../dependent-dropdown-filters.md) for commands,
guards, source traceability, acceptance gaps and activation/release gates.
The browser server is stopped after verification; synthetic databases and
artifacts are retained locally for review. Credentials remain in the separate
mode-`0600` fixture file, not this index or Git. Do not publish credential files,
raw session-bearing logs or unrelated data.

Outstanding: independent checker/HR-owner approval, approved combined-module
regression, external/portal integration review, realistic performance budgets,
wider concurrency/keyboard/mobile/accessibility cases, Odoo.sh/UAT and
backup/restore. The implementation record maps DDF-01–12 to local proof and
remaining gates; passing this suite is not an assertion that every standard is
certified.
