from odoo import fields, models


class CrmWonReason(models.Model):
    _name = "crm.won.reason"
    _description = "Opp. Won Reason"
    _rec_name = "s_name"
    _active_name = "is_active"

    s_name = fields.Char("Description", required=True, translate=True)
    is_active = fields.Boolean("Active", default=True)
    stage_ids = fields.Many2many(
        "crm.stage",
        string="Stages",
        help="Leave empty to allow this reason on every stage.",
    )
