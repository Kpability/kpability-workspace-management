from odoo import api, models


class DropdownAdapter(models.Model):
    _inherit = "dropdown.adapter"

    @api.model
    def _definitions(self):
        return {
            **super()._definitions(),
            "crm_sales_department": {"model": "crm.lead", "child": "user_id"},
            "contacts_sales_department": {"model": "res.partner", "child": "user_id"},
        }
