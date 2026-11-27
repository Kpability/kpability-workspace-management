from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


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
    s_domain = fields.Char(
        string="Condition",
        help="Optional domain on the lead/opportunity. If set, activity plans "
             "and email templates run only when the record matches this domain.",
    )
    n_activity_plan_count = fields.Integer(
        compute="_compute_counts",
    )
    n_mail_template_count = fields.Integer(
        compute="_compute_counts",
    )

    _stage_id_uniq = models.Constraint(
        "unique(stage_id)",
        "A template set already exists for this stage.",
    )

    def _compute_counts(self):
        for record in self:
            record.n_activity_plan_count = len(record.activity_plan_ids)
            record.n_mail_template_count = len(record.mail_template_ids)

    @api.constrains("stage_id")
    def _check_stage_id_uniq(self):
        for record in self:
            if not record.stage_id:
                continue
            duplicate = self.search_count([
                ("id", "!=", record.id),
                ("stage_id", "=", record.stage_id.id),
            ])
            if duplicate:
                raise ValidationError(self.env._(
                    "A template set already exists for stage \"%(stage)s\".",
                    stage=record.stage_id.display_name,
                ))

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
