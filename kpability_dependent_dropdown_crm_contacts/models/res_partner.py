from odoo import api, fields, models


class ResPartner(models.Model):
    _name = "res.partner"
    _inherit = ["res.partner", "dropdown.binding.mixin"]

    primary_contact_id = fields.Many2one(
        "res.partner", string="Primary Contact", check_company=True, ondelete="set null",
        help="Optional primary individual contact for this company. Never inferred or backfilled.",
    )
    j_dropdown_primary_contact_domain = fields.Json(
        compute="_compute_dropdown_primary_contact", compute_sudo=False, groups="base.group_user",
    )
    s_dropdown_primary_contact_hint = fields.Char(
        compute="_compute_dropdown_primary_contact", compute_sudo=False, groups="base.group_user",
    )

    def _dropdown_field_names(self):
        return (*super()._dropdown_field_names(), "primary_contact_id")

    @api.depends("primary_contact_id", "company_id", "is_company")
    @api.depends_context("company", "uid", "allowed_company_ids")
    def _compute_dropdown_primary_contact(self):
        for partner in self:
            domain, hint = self.env["dropdown.filters"]._get_state(partner, "primary_contact_id")
            partner.j_dropdown_primary_contact_domain = domain
            partner.s_dropdown_primary_contact_hint = hint
