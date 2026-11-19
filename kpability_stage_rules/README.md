# Stage Rules

Configure what people see, can edit, or must fill in on the standard Odoo CRM opportunity form. The add-on depends only on `crm` and does not require Studio.

1. As a CRM administrator, open **CRM → Configuration → Stage Rules**.
2. Select the stage and opportunity field. Leave **User Group** blank to apply the rule to everyone in the opportunity's company.
3. Choose **Visibility**, **Editing**, or **Requirement**. For a conditional option, pick a field, an operator, and a value if prompted.
4. Turn on **Active**, save the rule, and reopen an opportunity to try it.

For example, select **Expected Closing**, choose **Required when the condition matches**, then set the condition to **Priority → Is equal to → Very High**. Salespeople can preview changes by clicking the stage and use Odoo's existing **Save manually** and **Discard all changes** controls.

Rules apply only to the opportunity form, not to kanban, imports, automation, or API writes. They do not change what users have permission to access.

See [Stage Rules development and testing](docs/stage-rules.md) for supported fields, precedence, and verification commands.
