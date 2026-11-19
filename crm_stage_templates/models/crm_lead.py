import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        if not self.env.context.get("skip_crm_stage_templates"):
            leads.filtered("stage_id")._apply_stage_templates()
        return leads

    def write(self, vals):
        stage_before = (
            {lead.id: lead.stage_id.id for lead in self}
            if "stage_id" in vals
            else {}
        )
        res = super().write(vals)
        if (
            "stage_id" in vals
            and not self.env.context.get("skip_crm_stage_templates")
        ):
            changed = self.filtered(
                lambda lead: stage_before.get(lead.id) != lead.stage_id.id
            )
            changed._apply_stage_templates()
        return res

    def _apply_stage_templates(self):
        StageTemplate = self.env["crm.stage.template"].sudo()
        templates_by_stage = {
            template.stage_id.id: template
            for template in StageTemplate.search([
                ("stage_id", "in", self.stage_id.ids),
            ])
        }
        for lead in self:
            template = templates_by_stage.get(lead.stage_id.id)
            if not template:
                continue
            for plan in template.activity_plan_ids:
                lead._apply_stage_template_activity_plan(plan)
            for mail_template in template.mail_template_ids:
                lead._apply_stage_template_email(mail_template)

    def _apply_stage_template_activity_plan(self, plan):
        self.ensure_one()
        on_demand_user = self.user_id or self.env.user
        try:
            self.env["mail.activity.schedule"].with_context(
                active_model="crm.lead",
                active_id=self.id,
                active_ids=self.ids,
            ).create({
                "res_model": "crm.lead",
                "res_ids": f"[{self.id}]",
                "plan_id": plan.id,
                "plan_date": fields.Date.context_today(self),
                "plan_on_demand_user_id": on_demand_user.id,
                "activity_user_id_fname": "user_id",
            }).action_schedule_plan()
        except Exception:
            _logger.exception(
                "Failed to launch activity plan %s on lead %s",
                plan.display_name,
                self.id,
            )
            self.message_post(
                body=self.env._(
                    'Could not launch activity plan "%(plan)s" for this stage.',
                    plan=plan.display_name,
                )
            )

    def _apply_stage_template_email(self, mail_template):
        self.ensure_one()
        try:
            mail_template.send_mail(
                self.id,
                force_send=False,
                raise_exception=False,
            )
        except Exception:
            _logger.exception(
                "Failed to send email template %s on lead %s",
                mail_template.display_name,
                self.id,
            )
            self.message_post(
                body=self.env._(
                    'Could not send email template "%(template)s" for this stage.',
                    template=mail_template.display_name,
                )
            )
