# CRM / Contacts dependent dropdowns

Adds the explicitly approved Customer Company field in CRM and Primary Contact
field on Contacts company forms. No native field is renamed, inferred or backfilled.

Install this add-on for company/contact filtering without HR. It installs two
read-only supported-binding catalog entries, **not active filter records**.
Administrators configure one filter per tenant/binding in Settings → Technical
→ Dependent Dropdown Filters.

The native CRM Contact widgets retain their contexts. Both lead and opportunity
form occurrences use the same composed domain. Contacts reuses the same core for
Primary Contact in Sales & Purchase. Active direct-child individuals only are
eligible when the corresponding filter is enabled.

See [setup, behavior and compatibility boundaries](../kpability_dependent_dropdown_filters/README.md)
and the [implementation/test record](../kpability_dependent_dropdown_filters/docs/dependent-dropdown-filters.md).
