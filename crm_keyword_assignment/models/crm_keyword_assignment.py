from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval

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
    s_domain = fields.Char(
        string="Condition",
        help="Optional domain on the lead/opportunity. "
             "If set, the record must match this domain before the rule assigns a salesperson.",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Salesperson",
        required=True,
        domain=[("share", "=", False)],
    )

    @api.constrains("field_id")
    def _check_field_id(self):
        for rule in self:
            field = rule.field_id
            if (
                not field
                or field.model != "crm.lead"
                or not field.store
                or field.ttype not in SUPPORTED_FIELD_TYPES
            ):
                raise ValidationError(self.env._(
                    "Keyword Assignment only supports stored char, text, selection, "
                    "many2one, or many2many fields on Lead/Opportunity."
                ))

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
        self.ensure_one()
        if self.field_id.ttype not in SUPPORTED_FIELD_TYPES:
            return []
        field_name = self.field_id.name
        value = lead[field_name]
        if self.field_id.ttype in ("many2one", "many2many"):
            return value.mapped("display_name")
        if self.field_id.ttype == "selection":
            labels = dict(lead._fields[field_name]._description_selection(self.env))
            return [labels.get(value) or ""]
        if not isinstance(value, str):
            return []
        return [value]

    def _matches_domain(self, lead):
        self.ensure_one()
        if not self.s_domain or self.s_domain == "[]":
            return True
        try:
            domain = safe_eval(self.s_domain, {
                "uid": self.env.uid,
                "user": self.env.user,
                "context": dict(self.env.context),
            })
        except Exception:
            return False
        return bool(lead.filtered_domain(domain))

    def _matches(self, lead):
        self.ensure_one()
        if not self._matches_domain(lead):
            return False
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
