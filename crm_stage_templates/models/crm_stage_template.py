from odoo import fields, models


class CrmStageTemplate(models.Model):
    _name = "crm.stage.template"
    _description = "CRM Stage Template"
    _order = "n_sequence, id"
    _rec_name = "stage_id"

    n_sequence = fields.Integer("Sequence", default=10)
    active = fields.Boolean(default=True)
    stage_id = fields.Many2one(
        "crm.stage",
        string="Stage",
        required=True,
        ondelete="cascade",
        index=True,
    )
    activity_plan_ids = fields.Many2many(
        "mail.activity.plan",
        "crm_stage_template_activity_plan_rel",
        "stage_template_id",
        "activity_plan_id",
        string="Activity Plans",
        domain=[("res_model", "=", "crm.lead")],
    )
    mail_template_ids = fields.Many2many(
        "mail.template",
        "crm_stage_template_mail_template_rel",
        "stage_template_id",
        "mail_template_id",
        string="Email Templates",
        domain=[("model", "=", "crm.lead")],
    )
    s_stage_rules = fields.Text(
        "Stage Rules",
        help="Notes for stage rules (visible / enabled / required). "
             "Detailed Stage Rules automation can be linked here later.",
    )
    n_activity_plan_count = fields.Integer(
        compute="_compute_counts",
    )
    n_mail_template_count = fields.Integer(
        compute="_compute_counts",
    )

    _sql_constraints = [
        (
            "stage_id_uniq",
            "unique(stage_id)",
            "A template set already exists for this stage.",
        ),
    ]

    def _compute_counts(self):
        for record in self:
            record.n_activity_plan_count = len(record.activity_plan_ids)
            record.n_mail_template_count = len(record.mail_template_ids)
