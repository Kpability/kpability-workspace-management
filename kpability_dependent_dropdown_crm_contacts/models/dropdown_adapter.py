from odoo import api, models


class DropdownAdapter(models.Model):
    _inherit = "dropdown.adapter"

    @api.model
    def _definitions(self):
        return {
            **super()._definitions(),
            "crm_customer_contact": {
                "model": "crm.lead", "child": "partner_id", "parent": "customer_company_id",
                "inverse": "parent_id",
                "parent_domain": [("active", "=", True), ("is_company", "=", True)],
                "parent_is_company": True,
                "candidate_domain": [("active", "=", True), ("is_company", "=", False)],
            },
            "contacts_primary_contact": {
                "model": "res.partner", "child": "primary_contact_id", "parent": "id",
                "inverse": "parent_id",
                "parent_domain": [("active", "=", True), ("is_company", "=", True)],
                "parent_is_company": True,
                "candidate_domain": [("active", "=", True), ("is_company", "=", False)],
            },
        }
