from odoo import api, fields, models


class CrmLeadWon(models.TransientModel):
    _name = "crm.lead.won"
    _description = "Get Won Reason"

    lead_id = fields.Many2one("crm.lead", required=True, ondelete="cascade")
    stage_id = fields.Many2one(related="lead_id.stage_id")
    has_won_reasons = fields.Boolean(compute="_compute_has_won_reasons")
    won_reason_id = fields.Many2one(
        "crm.won.reason",
        string="Won Reason",
        required=True,
    )
    s_won_reason_custom = fields.Char("Details")

    @api.depends("stage_id")
    def _compute_has_won_reasons(self):
        for wizard in self:
            wizard.has_won_reasons = bool(self.env["crm.won.reason"].search_count(
                ["|", ("stage_ids", "=", False), ("stage_ids", "in", wizard.stage_id.ids)],
                limit=1,
            ))

    def action_won_reason_apply(self):
        self.ensure_one()
        self.lead_id.write({
            "won_reason_id": self.won_reason_id.id,
            "s_won_reason_custom": self.s_won_reason_custom,
        })
        action = {"type": "ir.actions.act_window_close"}
        result = self.lead_id.action_set_won_rainbowman()
        if isinstance(result, dict):
            action.update(result)
        return action
