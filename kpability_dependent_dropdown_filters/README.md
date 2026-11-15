# Dependent dropdown filters

Odoo 20 configuration foundation for supported dependent Many2one selectors.
This is not an arbitrary domain builder or a security/roles replacement.

## Add-ons

| Add-on | Purpose | Dependencies |
| --- | --- | --- |
| `kpability_dependent_dropdown_filters` | Maintained, company-scoped configuration and safe composition | `base`, `web` |
| `kpability_dependent_dropdown_crm_contacts` | Customer Company → CRM Contact; company → Contacts Primary Contact | Core, `crm`, `contacts` |
| `kpability_dependent_dropdown_hr` | Configured department → native CRM/Contacts Salesperson | CRM/Contacts adapter, `hr` |

**Installation does not activate any filter or change existing assignments.**
Only supported binding catalog records are installed. New filter records default
inactive. Do not activate rules on a company database without the review and
legacy-data checks below.

See the [implementation, source traceability and test record](docs/dependent-dropdown-filters.md)
and the [development plan](../docs/development/dependent-dropdown-filters.md).

## Configure in a disposable test database first

1. Install the appropriate adapter, not HR unless department filtering is needed.
2. As a Settings administrator, open Settings → Technical → Dependent Dropdown Filters.
3. Create a named filter, choose the tenant company and a supported binding.
   There is one maintained record per company/binding, including archived records.
4. For a department binding, choose the actual department record belonging to
   that tenant. Membership is exact, not recursive and not based on its name.
5. Review existing relationships, access and company restrictions before enabling
   Active. No migration, inference, default department or backfill runs.
6. Reopen affected forms after configuration/membership changes. A form already
   open is not pushed a live configuration update; saving a changed relationship
   always checks current configuration.

Filters narrow native domains with AND. ACLs, record rules, company consistency,
search pagination and native Save/Discard remain Odoo's responsibility.
Unresolved/unreadable parents and empty mappings never fall back to all records.

## Approved behavior

- CRM Customer Company is a new relational field. Native Company Name text and
  the tenant Company field retain their existing meanings.
- Contacts Primary Contact appears in Sales & Purchase on company records.
  A new company must first be saved; no autosave creates it for this selector.
- Individuals must be active, non-company direct children of the selected
  company. Grandchildren, archived records and inaccessible records are excluded.
- A stale selection stays visible under native access, with an explicit warning.
  Changing the relationship requires clear/reselection; unrelated legacy edits
  remain possible. Discard does not overwrite saved relationships.
- New or changed nonempty assignments are checked in create/write, including
  import/RPC. A public context flag cannot disable validation.
- The optional HR adapter requires an active internal user linked to an active
  public employee in the exact configured department and tenant company. It
  grants no private employee permissions and uses neither `sudo` nor `any!`.
- Deactivation stops the configured restriction without rewriting records.
  Creation shortcuts remain disabled on the installed supported form selectors;
  removing the view extension restores those shortcuts.

## Compatibility boundaries

Only the listed native form selectors are adapted. Kanban quick creation,
alternative/custom views and future XML/Python domain extensions require their
own compatibility review; backend checks still apply to changed assignments.
No arbitrary expressions, multi-hop cascades, global `name_search` override,
cross-company configuration or runtime code snippets are supported.

Changes to contact hierarchy, department membership or configuration do not
rewrite historical documents. Warnings appear on reopening; enforcement applies
when the document's relationship changes. Configuration is not an access grant.
External/portal integrations and combined optional modules are not certified by
the internal-user tests. Independent review, realistic performance, Odoo.sh/UAT,
backup/restore and approved deployment remain outstanding.
