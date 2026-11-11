from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = "crm.lead.lost"

    lead_stage_ids = fields.Many2many(
        "crm.stage",
        compute="_compute_lead_stage_ids",
    )
    s_lost_reason_custom = fields.Char("Other Reason")

    @api.depends("lead_ids")
    def _compute_lead_stage_ids(self):
        for wizard in self:
            wizard.lead_stage_ids = wizard.lead_ids.stage_id

    @api.onchange("lost_reason_id")
    def _onchange_lost_reason_id(self):
        if self.lost_reason_id:
            self.s_lost_reason_custom = False

    def action_lost_reason_apply(self):
        self.lead_ids.s_lost_reason_custom = self.s_lost_reason_custom
        return super().action_lost_reason_apply()
