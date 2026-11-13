from odoo import api, fields, models


class CrmLeadLost(models.TransientModel):
    _inherit = "crm.lead.lost"

    lead_stage_ids = fields.Many2many(
        "crm.stage",
        compute="_compute_lead_stage_ids",
    )
    has_lost_reasons = fields.Boolean(compute="_compute_has_lost_reasons")
    s_lost_reason_custom = fields.Char("Details")

    @api.depends("lead_ids")
    def _compute_lead_stage_ids(self):
        for wizard in self:
            wizard.lead_stage_ids = wizard.lead_ids.stage_id

    @api.depends("lead_stage_ids")
    def _compute_has_lost_reasons(self):
        for wizard in self:
            wizard.has_lost_reasons = bool(self.env["crm.lost.reason"].search_count(
                ["|", ("stage_ids", "=", False), ("stage_ids", "in", wizard.lead_stage_ids.ids)],
                limit=1,
            ))

    def action_lost_reason_apply(self):
        self.lead_ids.s_lost_reason_custom = self.s_lost_reason_custom
        return super().action_lost_reason_apply()
