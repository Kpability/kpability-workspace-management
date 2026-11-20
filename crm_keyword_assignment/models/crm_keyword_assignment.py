from odoo import api, fields, models

SUPPORTED_FIELD_TYPES = ("char", "text", "selection", "many2one", "many2many")


class CrmKeywordAssignment(models.Model):
    _name = "crm.keyword.assignment"
    _description = "CRM Keyword Assignment Rule"
    _order = "n_sequence, id"

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
    keyword_ids = fields.Many2many(
        "crm.keyword",
        "crm_keyword_assignment_keyword_rel",
        "assignment_id",
        "keyword_id",
        string="Keywords",
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        required=True,
        domain=[("share", "=", False)],
    )

    @api.depends("keyword_ids.s_name")
    def _compute_display_name(self):
        for record in self:
            record.display_name = ", ".join(record.keyword_ids.mapped("s_name")) or record.env._(
                "Keyword Rule"
            )

    def _get_keywords(self):
        self.ensure_one()
        return [
            name.strip().lower()
            for name in self.keyword_ids.mapped("s_name")
            if name and name.strip()
        ]

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
        keywords = self._get_keywords()
        if not keywords:
            return False
        values = [
            value.strip().lower()
            for value in self._get_lead_values(lead)
            if value
        ]
        return any(
            self._compare(value, keyword)
            for value in values
            for keyword in keywords
        )

    def _compare(self, value, keyword):
        if self.e_comparison_type == "equals":
            return value == keyword
        if self.e_comparison_type == "starts_with":
            return value.startswith(keyword)
        if self.e_comparison_type == "ends_with":
            return value.endswith(keyword)
        return keyword in value
