# Optional department / salesperson adapter

Requires HR and the CRM/Contacts adapter. It adds department bindings for the
native CRM and Contacts Salesperson fields. Installing it creates no filter,
default department, employee or assignment.

Administrators choose an explicit department per tenant company. Eligibility is
active internal user AND active public employee AND exact configured department
AND matching tenant company, intersected with native restrictions. A department
named Sales is not a lookup rule. Subdepartments are not included.

The resolver uses native `hr.employee.public` through
`res.users.employee_public_ids` with access-respecting `any`, not private HR,
`sudo`, `any!`, or a precomputed list of all eligible user IDs. No new private-HR
access is granted. Missing configuration/access must not broaden a list.

Verify ordinary sales-user access and the HR/data owner's policy before any
company activation. See the [core setup](../kpability_dependent_dropdown_filters/README.md)
and [source/test record](../kpability_dependent_dropdown_filters/docs/dependent-dropdown-filters.md).
