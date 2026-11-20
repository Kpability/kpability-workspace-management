from odoo import SUPERUSER_ID, Command, api, fields


LEGACY_OPERATORS = {
    "equals": "=", "not_equals": "!=", "before": "<", "after": ">",
    "is_set": "!=", "is_not_set": "=",
}


def migrate(cr, version):
    env = api.Environment(cr, SUPERUSER_ID, {})
    rules = env["stage.rules"]
    registered = {
        field.s_field_name: field.id for field in env["stage.rules.field"].search([])
    }
    cr.execute("""
        SELECT id, stage_id, group_id, e_target_field, e_visibility, e_enabled, e_required,
               e_condition_field, e_operator, e_priority, s_compare_text, d_compare_date
          FROM stage_rules WHERE stage_id IS NOT NULL
    """)
    for old in cr.dictfetchall():
        values = {
            "stage_ids": [Command.set([old["stage_id"]])],
            "target_field_ids": [Command.set([registered[old["e_target_field"]]])],
            "group_ids": [Command.set([old["group_id"]] if old["group_id"] else [])],
        }
        for behavior in ("visibility", "enabled", "required"):
            if old[f"e_{behavior}"] != "when":
                continue
            name, operator = old["e_condition_field"], old["e_operator"]
            if operator in {"is_set", "is_not_set"}:
                operand = False
            elif name == "priority":
                operand = old["e_priority"]
            elif name == "date_deadline":
                operand = fields.Date.to_string(old["d_compare_date"])
            else:
                operand = old["s_compare_text"].strip()
            domain = [(name, LEGACY_OPERATORS[operator], operand)]
            if operator == "not_equals":
                domain.insert(0, (name, "!=", False))
            values[f"s_{behavior}_domain"] = repr(domain)
        rules.browse(old["id"]).write(values)
    cr.execute("""
        ALTER TABLE stage_rules
            DROP COLUMN stage_id, DROP COLUMN group_id, DROP COLUMN e_target_field,
            DROP COLUMN e_condition_field, DROP COLUMN e_operator, DROP COLUMN e_priority,
            DROP COLUMN s_compare_text, DROP COLUMN d_compare_date
    """)
