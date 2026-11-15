from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    j_dropdown_salesperson_domain = fields.Json(
        compute="_compute_dropdown_salesperson", compute_sudo=False, groups="base.group_user",
    )
    s_dropdown_salesperson_hint = fields.Char(
        compute="_compute_dropdown_salesperson", compute_sudo=False, groups="base.group_user",
    )

    def _dropdown_field_names(self):
        return (*super()._dropdown_field_names(), "user_id")

    @api.depends("user_id", "company_id")
    @api.depends_context("company", "uid", "allowed_company_ids")
    def _compute_dropdown_salesperson(self):
        for lead in self:
            domain, hint = self.env["dropdown.filters"]._get_state(lead, "user_id")
            lead.j_dropdown_salesperson_domain = domain
            lead.s_dropdown_salesperson_hint = hint


class ResPartner(models.Model):
    _inherit = "res.partner"

    j_dropdown_salesperson_domain = fields.Json(
        compute="_compute_dropdown_salesperson", compute_sudo=False, groups="base.group_user",
    )
    s_dropdown_salesperson_hint = fields.Char(
        compute="_compute_dropdown_salesperson", compute_sudo=False, groups="base.group_user",
    )

    def _dropdown_field_names(self):
        return (*super()._dropdown_field_names(), "user_id")

    @api.depends("user_id", "company_id")
    @api.depends_context("company", "uid", "allowed_company_ids")
    def _compute_dropdown_salesperson(self):
        for partner in self:
            domain, hint = self.env["dropdown.filters"]._get_state(partner, "user_id")
            partner.j_dropdown_salesperson_domain = domain
            partner.s_dropdown_salesperson_hint = hint
