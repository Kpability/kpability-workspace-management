from lxml import etree

from odoo import api, fields, models
from odoo.exceptions import ValidationError


TARGET_TYPES = {
    "boolean", "char", "date", "datetime", "float", "integer", "many2many",
    "many2one", "monetary", "selection", "text",
}
SCOPE_FIELDS = {"company_id", "id", "stage_id", "type"}


class StageRulesField(models.Model):
    _name = "stage.rules.field"
    _description = "Registered CRM Opportunity Field"
    _rec_name = "s_name"
    _order = "s_name, id"

    s_name = fields.Char(string="Label", compute="_compute_name", store=True)
    s_field_name = fields.Char(string="CRM Field", required=True, copy=False)

    _unique_field = models.Constraint("UNIQUE(s_field_name)", "This CRM field is already registered.")

    @api.model
    def _opportunity_fields(self):
        lead = self.env["crm.lead"]
        lead.check_access("read")
        arch = etree.fromstring(lead.get_view(self.env.ref("crm.crm_lead_view_form").id)["arch"])
        form_names = set(arch.xpath("//field[not(ancestor::field)]/@name"))
        return {
            name: info for name, info in lead.fields_get(form_names, ["type", "string"]).items()
            if info["type"] in TARGET_TYPES
        }

    @api.model
    def get_field_choices(self):
        """Limit the visual pickers to fields present on this user's CRM form."""
        self.check_access("read")
        registered = set(self.with_context(active_test=False).search([]).mapped("s_field_name"))
        return sorted(set(self._opportunity_fields()) - SCOPE_FIELDS - registered)

    @api.depends("s_field_name")
    def _compute_name(self):
        field_names = self.mapped("s_field_name")
        descriptions = self.env["crm.lead"].with_context(lang="en_US").fields_get(field_names, ["string"])
        for registered_field in self:
            name = registered_field.s_field_name
            registered_field.s_name = descriptions.get(name, {}).get("string") or name

    @api.constrains("s_field_name")
    def _check_registered_field(self):
        allowed = self._opportunity_fields()
        for registered_field in self:
            if registered_field.s_field_name in SCOPE_FIELDS or registered_field.s_field_name not in allowed:
                raise ValidationError(self.env._(
                    "Select a supported field already present on the CRM opportunity form. "
                    "Stage, Company, and Opportunity Type cannot be rule targets."
                ))

    def write(self, values):
        if "s_field_name" in values and any(
            field.s_field_name != values["s_field_name"] for field in self
        ):
            raise ValidationError(self.env._("Register a new CRM field instead of changing an existing one."))
        return super().write(values)
