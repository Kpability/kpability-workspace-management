from odoo import api, fields, models


class CrmLead(models.Model):
    _name = "crm.lead"
    _inherit = ["crm.lead", "dropdown.binding.mixin"]

    customer_company_id = fields.Many2one(
        "res.partner", string="Customer Company", check_company=True,
        domain=[("is_company", "=", True), ("active", "=", True)],
        help="Customer company used by an explicitly activated contact dropdown filter. "
             "This is not the tenant company or the native Company Name text.",
    )
    j_dropdown_contact_domain = fields.Json(
        compute="_compute_dropdown_contact", compute_sudo=False, groups="base.group_user",
    )
    s_dropdown_contact_hint = fields.Char(
        compute="_compute_dropdown_contact", compute_sudo=False, groups="base.group_user",
    )

    def _dropdown_field_names(self):
        return (*super()._dropdown_field_names(), "partner_id")

    @api.depends("customer_company_id", "partner_id", "company_id")
    @api.depends_context("company", "uid", "allowed_company_ids")
    def _compute_dropdown_contact(self):
        for lead in self:
            domain, hint = self.env["dropdown.filters"]._get_state(lead, "partner_id")
            lead.j_dropdown_contact_domain = domain
            lead.s_dropdown_contact_hint = hint
