from odoo import fields, models


class CrmLostReason(models.Model):
    _inherit = "crm.lost.reason"

    stage_ids = fields.Many2many(
        "crm.stage",
        string="Stages",
        help="Leave empty to allow this reason on every stage.",
    )
