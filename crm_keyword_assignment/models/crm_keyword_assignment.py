from odoo import fields, models

SUPPORTED_FIELD_TYPES = ("char", "text", "selection", "many2one", "many2many")


class CrmKeywordAssignment(models.Model):
    _name = "crm.keyword.assignment"
    _description = "CRM Keyword Assignment Rule"
    _order = "n_sequence, id"
    _rec_name = "s_keyword"

    n_sequence = fields.Integer("Sequence", default=10)
    active = fields.Boolean(default=True)
    field_id = fields.Many2one(
        "ir.model.fields",
        string="Field",
        required=True,
        ondelete="cascade",
        domain=[
            ("model", "=", "crm.lead"),
            ("ttype", "in", SUPPORTED_FIELD_TYPES),
            ("store", "=", True),
        ],
    )
    e_comparison_type = fields.Selection(
        [
            ("equals", "Equals"),
            ("contains", "Contains"),
            ("starts_with", "Starts With"),
            ("ends_with", "Ends With"),
        ],
        string="Comparison Type",
        required=True,
        default="contains",
    )
    s_keyword = fields.Char("Keyword", required=True)
    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        required=True,
        domain=[("share", "=", False)],
    )

    def _get_lead_values(self, lead):
        field_name = self.field_id.name
        value = lead[field_name]
        if self.field_id.ttype in ("many2one", "many2many"):
            return value.mapped("display_name")
        if self.field_id.ttype == "selection":
            labels = dict(lead._fields[field_name]._description_selection(self.env))
            return [labels.get(value) or ""]
        return [value or ""]

    def _matches(self, lead):
        self.ensure_one()
        keyword = self.s_keyword.strip().lower()
        return bool(keyword) and any(
            self._compare(value.strip().lower(), keyword)
            for value in self._get_lead_values(lead)
            if value
        )

    def _compare(self, value, keyword):
        if self.e_comparison_type == "equals":
            return value == keyword
        if self.e_comparison_type == "starts_with":
            return value.startswith(keyword)
        if self.e_comparison_type == "ends_with":
            return value.endswith(keyword)
        return keyword in value
