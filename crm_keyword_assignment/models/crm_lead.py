from odoo import api, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        to_assign = self.browse([
            lead.id
            for lead, vals in zip(leads, vals_list)
            if not vals.get("user_id")
        ])
        to_assign._apply_keyword_assignment()
        return leads

    def write(self, vals):
        res = super().write(vals)
        if "user_id" not in vals:
            self._apply_keyword_assignment()
        return res

    def _get_keyword_assignment_rules(self):
        return self.env["crm.keyword.assignment"].sudo().search([])

    def _apply_keyword_assignment(self, rules=None):
        if rules is None:
            rules = self._get_keyword_assignment_rules()
        if not rules:
            return
        for lead in self:
            rule = next((rule for rule in rules if rule._matches(lead)), None)
            if rule and lead.user_id != rule.user_id:
                lead.sudo().user_id = rule.user_id
