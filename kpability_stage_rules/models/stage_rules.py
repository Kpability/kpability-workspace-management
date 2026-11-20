from ast import literal_eval
from math import isfinite

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.fields import Domain

from .stage_rules_field import SCOPE_FIELDS


EQUALITY = {"=", "!="}
MEMBERSHIP = {"in", "not in"}
ORDERING = {"<", "<=", ">", ">="}
TEXT_MATCH = {"ilike", "not ilike"}
OPERATORS_BY_TYPE = {
    "boolean": EQUALITY,
    "char": EQUALITY | TEXT_MATCH,
    "text": EQUALITY | TEXT_MATCH,
    "selection": EQUALITY | MEMBERSHIP,
    "date": EQUALITY | ORDERING,
    "datetime": EQUALITY | ORDERING,
    "float": EQUALITY | ORDERING,
    "integer": EQUALITY | ORDERING,
    "monetary": EQUALITY | ORDERING,
    "many2one": EQUALITY | MEMBERSHIP,
    "many2many": EQUALITY | MEMBERSHIP,
}
BEHAVIORS = ("visibility", "enabled", "required")


def _valid_operand(field_type, operator, value):
    if operator in MEMBERSHIP:
        return (
            isinstance(value, (list, tuple)) and len(value) <= 200
            and all(
                (type(item) is int and item > 0)
                if field_type in {"many2one", "many2many"} else type(item) in {int, str}
                for item in value
            )
        )
    if value is False:
        return operator in EQUALITY
    if field_type == "boolean":
        return type(value) is bool
    if field_type in {"many2one", "many2many"}:
        return type(value) is int and value > 0 and field_type != "many2many"
    if field_type in {"integer", "float", "monetary"}:
        return type(value) is int or type(value) is float and isfinite(value)
    if field_type == "selection":
        return type(value) in {int, str}
    if not isinstance(value, str):
        return False
    if field_type in {"date", "datetime"}:
        converter = fields.Date if field_type == "date" else fields.Datetime
        try:
            return converter.to_string(converter.to_date(value) if field_type == "date"
                                       else converter.to_datetime(value)) == value
        except (TypeError, ValueError):
            return False
    return True


class StageRules(models.Model):
    _name = "stage.rules"
    _description = "CRM Opportunity Stage Rule"
    _rec_name = "s_name"
    _order = "company_id, s_name, id"

    s_name = fields.Char(string="Rule Name", required=True)
    active = fields.Boolean(default=False, help="Only active rules apply to opportunities.")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, ondelete="cascade",
        help="The company on the opportunity, not the company selected in the top bar.",
    )
    stage_ids = fields.Many2many("crm.stage", string="Stages", required=True, ondelete="restrict")
    target_field_ids = fields.Many2many(
        "stage.rules.field", string="Opportunity Fields", required=True, ondelete="restrict",
        help="If a field is missing, type in the dropdown and choose Create and edit to register it.",
    )
    group_ids = fields.Many2many(
        "res.groups", string="User Groups", ondelete="restrict",
        help="Leave empty for everyone. Otherwise, users in any selected group qualify, including through implied membership.",
    )
    e_visibility = fields.Selection(
        [("inherit", "Use Odoo default"), ("hidden", "Hide"), ("when", "Show only when the condition matches")],
        string="Visibility", required=True, default="inherit",
    )
    e_enabled = fields.Selection(
        [("inherit", "Use Odoo default"), ("disabled", "Read-only"), ("when", "Editable only when the condition matches")],
        string="Editing", required=True, default="inherit",
    )
    e_required = fields.Selection(
        [("inherit", "Use Odoo default"), ("always", "Required"), ("when", "Required when the condition matches")],
        string="Requirement", required=True, default="inherit",
    )
    s_visibility_domain = fields.Text(string="Visibility condition")
    s_enabled_domain = fields.Text(string="Editing condition")
    s_required_domain = fields.Text(string="Requirement condition")
    j_condition_fields = fields.Json(compute="_compute_condition_choices")

    @api.depends("target_field_ids")
    def _compute_condition_choices(self):
        available = set(self.env["stage.rules.field"]._opportunity_fields()) - {"id", "type"}
        for rule in self:
            rule.j_condition_fields = {
                "all": sorted(available),
                "non_targets": sorted(available - set(rule.target_field_ids.mapped("s_field_name"))),
            }

    @api.model
    def _condition_domain(self, domain_text):
        if not domain_text or len(domain_text) > 8192:
            raise ValidationError(self.env._("Add at least one condition for each conditional behavior."))
        try:
            terms = literal_eval(domain_text)
            if not isinstance(terms, (tuple, list)) or not terms or len(terms) > 100:
                raise ValueError
            for term in terms:
                if isinstance(term, str) and term in {"!", "|", "&"}:
                    continue
                if (
                    not isinstance(term, (list, tuple)) or len(term) != 3
                    or not isinstance(term[0], str) or not isinstance(term[1], str)
                ):
                    raise ValueError
            # Validate the prefix structure without evaluating any configuration as code.
            Domain(terms)
        except (TypeError, ValueError, SyntaxError, RecursionError) as error:
            raise ValidationError(self.env._("Enter a valid condition using the condition builder.")) from error
        return terms

    @api.constrains(
        "active", "stage_ids", "target_field_ids", "e_visibility", "e_enabled", "e_required",
        "s_visibility_domain", "s_enabled_domain", "s_required_domain",
    )
    def _check_rule_settings(self):
        available_fields = None
        for rule in self:
            if not rule.stage_ids or not rule.target_field_ids:
                raise ValidationError(self.env._("Choose at least one stage and one opportunity field."))
            modes = {behavior: rule[f"e_{behavior}"] for behavior in BEHAVIORS}
            if rule.active and set(modes.values()) == {"inherit"}:
                raise ValidationError(self.env._("Choose at least one change before activating this rule."))
            if rule.e_required != "inherit" and (
                rule.e_visibility == "hidden" or rule.e_enabled == "disabled"
            ):
                raise ValidationError(self.env._("Do not always hide or lock a field that this rule requires."))
            target_names = set(rule.target_field_ids.mapped("s_field_name"))
            for behavior, mode in modes.items():
                if mode != "when":
                    continue
                if available_fields is None:
                    available_fields = self.env["stage.rules.field"]._opportunity_fields()
                for term in rule._condition_domain(rule[f"s_{behavior}_domain"]):
                    if isinstance(term, str):
                        continue
                    name, operator, operand = term
                    field_type = available_fields.get(name, {}).get("type")
                    is_self_restriction = behavior != "required" and name in target_names
                    if (
                        name in {"id", "type"}
                        or operator not in OPERATORS_BY_TYPE.get(field_type, ())
                        or not _valid_operand(field_type, operator, operand)
                        or is_self_restriction
                    ):
                        raise ValidationError(self.env._(
                            "Choose a supported CRM form field and comparison. Visibility and editing "
                            "conditions cannot depend on a field that the same rule controls."
                        ))

    def _form_payload(self, readable_fields):
        self.ensure_one()
        field_names = [
            name for name in self.target_field_ids.mapped("s_field_name")
            if name in readable_fields and name not in SCOPE_FIELDS
        ]
        if not field_names:
            return None
        behaviors = {}
        for behavior in BEHAVIORS:
            mode = self[f"e_{behavior}"]
            if mode == "inherit":
                continue
            terms = self._condition_domain(self[f"s_{behavior}_domain"]) if mode == "when" else None
            if terms and any(
                not isinstance(term, str) and term[1] not in OPERATORS_BY_TYPE.get(
                    readable_fields.get(term[0], {}).get("type"), ()
                )
                for term in terms
            ):
                continue
            behaviors[behavior] = {"mode": mode, "domain": terms}
        if not behaviors:
            return None
        return {
            "company_id": self.company_id.id,
            "stage_ids": self.stage_ids.ids,
            "field_names": field_names,
            "behaviors": behaviors,
        }
