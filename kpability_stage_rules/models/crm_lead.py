from odoo import api, models

from .stage_rules import CONDITION_FIELDS


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
        readable_fields = self.fields_get(CONDITION_FIELDS, ["type"])
        # Salespeople cannot read configuration directly. Limit the privileged lookup
        # to active settings for their enabled companies and effective Odoo groups.
        rules = self.env["stage.rules"].sudo().search([
            ("active", "=", True),
            ("company_id", "in", company_ids),
            ("e_target_field", "in", list(readable_fields)),
            "|", ("group_id", "=", False), ("group_id", "in", group_ids),
        ])
        return [
            rule._form_payload() for rule in rules
            if not rule._uses_condition() or rule.e_condition_field in readable_fields
        ]
