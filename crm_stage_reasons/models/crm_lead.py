from odoo import fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    won_reason_id = fields.Many2one(
        "crm.won.reason",
        string="Won Reason",
        index=True,
        ondelete="restrict",
        tracking=True,
    )
    s_won_reason_custom = fields.Char("Won Reason Details", tracking=True)
    s_lost_reason_custom = fields.Char("Lost Reason Details", tracking=True)
