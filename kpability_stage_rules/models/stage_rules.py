from odoo import api, fields, models
from odoo.exceptions import ValidationError


TARGET_FIELDS = (
    "date_deadline", "user_id", "campaign_id", "medium_id", "source_id", "referred",
)
CONDITION_FIELDS = (
    "priority", "date_deadline", "user_id", "campaign_id", "medium_id", "source_id", "referred",
)
PRESENCE_OPERATORS = {"is_set", "is_not_set"}
COMPARISON_OPERATORS = {"equals", "not_equals"}
DATE_OPERATORS = COMPARISON_OPERATORS | {"before", "after"}


class StageRules(models.Model):
    _name = "stage.rules"
    _description = "CRM Opportunity Stage Rule"
    _rec_name = "s_name"
    _order = "company_id, stage_id, s_name, id"

    s_name = fields.Char(string="Rule Name", required=True)
    active = fields.Boolean(default=False, help="Only active rules apply to opportunities.")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, ondelete="cascade",
        help="The company on the opportunity, not the company selected in the top bar.",
    )
    stage_id = fields.Many2one("crm.stage", required=True, ondelete="cascade")
    group_id = fields.Many2one(
        "res.groups", string="Applies To", ondelete="restrict",
        help="Leave empty for everyone. Includes users who inherit the selected group.",
    )
    e_target_field = fields.Selection(
        selection="_selection_target_fields", string="Opportunity Field", required=True,
    )
    e_visibility = fields.Selection(
        [
            ("inherit", "Use Odoo default"),
            ("hidden", "Hide"),
            ("when", "Show only when the condition matches"),
        ],
        string="Visibility", required=True, default="inherit",
    )
    e_enabled = fields.Selection(
        [
            ("inherit", "Use Odoo default"),
            ("disabled", "Read-only"),
            ("when", "Editable only when the condition matches"),
        ],
        string="Editing", required=True, default="inherit",
    )
    e_required = fields.Selection(
        [
            ("inherit", "Use Odoo default"),
            ("always", "Required"),
            ("when", "Required when the condition matches"),
        ],
        string="Requirement", required=True, default="inherit",
    )
    e_condition_field = fields.Selection(
        selection="_selection_condition_fields", string="Condition Field",
    )
    e_operator = fields.Selection(
        [
            ("is_set", "Is set"),
            ("is_not_set", "Is not set"),
            ("equals", "Is equal to"),
            ("not_equals", "Is not equal to"),
            ("before", "Is before"),
            ("after", "Is after"),
        ],
        string="Operator",
    )
    j_allowed_operators = fields.Json(compute="_compute_allowed_operators")
    e_priority = fields.Selection(selection="_selection_priorities", string="Priority")
    s_compare_text = fields.Char(string="Text")
    d_compare_date = fields.Date(string="Date")

    _unique_active_scope = models.UniqueIndex(
        "(company_id, stage_id, e_target_field, group_id) NULLS NOT DISTINCT WHERE active",
        "An active rule already exists for this company, stage, field, and audience.",
    )

    @api.model
    def _selection_target_fields(self):
        return self._crm_field_labels(TARGET_FIELDS)

    @api.model
    def _selection_condition_fields(self):
        return self._crm_field_labels(CONDITION_FIELDS)

    @api.model
    def _crm_field_labels(self, field_names):
        descriptions = self.env["crm.lead"].fields_get(field_names, ["string"])
        return [(name, descriptions[name]["string"]) for name in field_names if name in descriptions]

    @api.model
    def _selection_priorities(self):
        return self.env["crm.lead"].fields_get(["priority"], ["selection"])["priority"]["selection"]

    @api.model
    def _operators_for(self, condition_field):
        if condition_field not in CONDITION_FIELDS:
            return set()
        if condition_field == "date_deadline":
            return PRESENCE_OPERATORS | DATE_OPERATORS
        if condition_field in {"referred", "priority"}:
            return COMPARISON_OPERATORS | (PRESENCE_OPERATORS if condition_field == "referred" else set())
        return PRESENCE_OPERATORS

    @api.depends("e_condition_field")
    def _compute_allowed_operators(self):
        for rule in self:
            rule.j_allowed_operators = sorted(rule._operators_for(rule.e_condition_field))

    def _uses_condition(self):
        self.ensure_one()
        return "when" in (self.e_visibility, self.e_enabled, self.e_required)

    @api.onchange("e_condition_field")
    def _onchange_condition_field(self):
        self.e_operator = (
            "equals" if self.e_condition_field == "priority"
            else "is_set" if self.e_condition_field else False
        )
        self.e_priority = False
        self.s_compare_text = False
        self.d_compare_date = False

    @api.onchange("e_operator")
    def _onchange_operator(self):
        if self.e_operator in PRESENCE_OPERATORS:
            self.e_priority = False
            self.s_compare_text = False
            self.d_compare_date = False

    @api.constrains(
        "active", "e_target_field", "e_visibility", "e_enabled", "e_required",
        "e_condition_field", "e_operator", "e_priority", "s_compare_text", "d_compare_date",
    )
    def _check_rule_settings(self):
        for rule in self:
            if rule.e_required != "inherit" and (
                rule.e_visibility == "hidden" or rule.e_enabled == "disabled"
                or (
                    rule.e_required == "always"
                    and "when" in (rule.e_visibility, rule.e_enabled)
                )
            ):
                raise ValidationError(self.env._(
                    "Keep the field visible and editable whenever it is required. "
                    "Change its visibility, editing, or requirement."
                ))
            if rule.active and {rule.e_visibility, rule.e_enabled, rule.e_required} == {"inherit"}:
                raise ValidationError(self.env._("Choose at least one change before activating this rule."))
            if not rule._uses_condition():
                continue
            if rule.e_condition_field == rule.e_target_field:
                raise ValidationError(self.env._("Choose a different field for the condition."))
            if rule.e_operator not in self._operators_for(rule.e_condition_field):
                raise ValidationError(self.env._("Choose a condition field and an operator valid for that field."))
            if rule.e_operator in PRESENCE_OPERATORS:
                continue
            if rule.e_condition_field == "priority" and not rule.e_priority:
                raise ValidationError(self.env._("Choose the priority to compare."))
            if rule.e_condition_field == "referred" and not (rule.s_compare_text or "").strip():
                raise ValidationError(self.env._("Enter the text to compare."))
            if rule.e_condition_field == "date_deadline" and not rule.d_compare_date:
                raise ValidationError(self.env._("Enter the date to compare."))

    def _form_payload(self):
        self.ensure_one()
        j_condition = False
        if self._uses_condition():
            j_condition = {"field_name": self.e_condition_field, "operator": self.e_operator}
            if self.e_operator not in PRESENCE_OPERATORS:
                if self.e_condition_field == "priority":
                    j_condition["value"] = self.e_priority
                elif self.e_condition_field == "date_deadline":
                    j_condition["value"] = fields.Date.to_string(self.d_compare_date)
                else:
                    j_condition["value"] = self.s_compare_text.strip()
        return {
            "company_id": self.company_id.id,
            "stage_id": self.stage_id.id,
            "field_name": self.e_target_field,
            "visibility": self.e_visibility,
            "enabled": self.e_enabled,
            "required": self.e_required,
            "condition": j_condition,
        }
