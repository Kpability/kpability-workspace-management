from odoo import api, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model
    def get_stage_rules_for_form(self):
        """Return applicable presentation settings, not configuration records or CRM data."""
        self.check_access("read")
        if not self.env.user.has_group("sales_team.group_sale_salesman"):
            return []

        company_ids = self.env.companies.ids
        group_ids = self.env.user.all_group_ids.ids
        readable_fields = self.fields_get(attributes=["type"])
        # Salespeople cannot read configuration directly. Limit the privileged lookup
        # to active settings for their enabled companies and effective Odoo groups.
        rules = self.env["stage.rules"].sudo().search([
            ("active", "=", True),
            ("company_id", "in", company_ids),
            "|", ("group_ids", "=", False), ("group_ids", "in", group_ids),
        ])
        return [
            payload for rule in rules if (payload := rule._form_payload(readable_fields))
        ]
