from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain


class CrmLead(models.Model):
    _inherit = "crm.lead"

    pipeline_team_category_ids = fields.Many2many(
        related="team_id.pipeline_category_ids",
        string="Team Categories",
        compute_sudo=False,
    )
    pipeline_category_id = fields.Many2one(
        domain="[('active', '=', True), ('id', 'in', pipeline_team_category_ids), "
               "('company_id', 'in', [False, company_id])]",
    )

    def _pipeline_team_assignment_key(self):
        self.ensure_one()
        # Reading stored computed fields forces native user/team/company/stage
        # recomputation before comparing final values, not merely incoming vals.
        return (self.pipeline_category_id.id, self.team_id.id, self.company_id.id, self.stage_id.id)

    def _check_pipeline_team_assignment(self, require_active=False):
        for lead in self.filtered("pipeline_category_id"):
            team, category = lead.team_id, lead.pipeline_category_id
            team.check_access("read")
            category.check_access("read")
            if not team or category not in team.pipeline_category_ids:
                raise ValidationError(_(
                    "Choose a sales team mapped to the selected pipeline category, select a category mapped to that team, "
                    "or explicitly clear the category. Missing teams and empty mappings do not allow categorized assignments."
                ))
            if category.company_id and category.company_id != team.company_id:
                raise ValidationError(_("The category must be shared or belong to the sales team's company."))
            if require_active:
                category._check_assignable()
                if not team.active:
                    raise ValidationError(_("Archived sales teams cannot receive new categorized assignments. Choose an active team."))

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads._check_pipeline_team_assignment(require_active=True)
        return leads

    def write(self, vals):
        # Unrelated edits on legacy/historical records remain possible. Routing
        # and stage changes must satisfy the new invariant after native computes.
        relevant = {"pipeline_category_id", "team_id", "company_id", "stage_id", "user_id", "partner_id", "type"}
        if not relevant.intersection(vals):
            return super().write(vals)
        previous = {lead.id: lead._pipeline_team_assignment_key() for lead in self}
        result = super().write(vals)
        for lead in self:
            current = lead._pipeline_team_assignment_key()
            if current != previous[lead.id]:
                lead._check_pipeline_team_assignment(require_active=current[:2] != previous[lead.id][:2])
        return result

    @api.onchange("team_id", "pipeline_category_id")
    def _onchange_pipeline_team_category(self):
        if self.pipeline_category_id and self.pipeline_category_id not in self.team_id.pipeline_category_ids:
            return {"warning": {
                "title": _("Category not available to this team"),
                "type": "notification",
                "message": _(
                    "The category has been kept. Choose a mapped team/category or explicitly clear the category before saving. "
                    "Native sales-team changes may still recompute the stage."
                ),
            }}

    @api.model
    def action_open_pipeline_team_compatibility(self):
        """Read-only, record-rule-aware rollout report; never repair or sudo."""
        if not self.env.user.has_group("sales_team.group_sale_manager"):
            raise AccessError(_("Only Sales Managers may open the pipeline compatibility report."))
        categories = self.env["crm.pipeline.category"].with_context(active_test=False).search([])
        teams = self.env["crm.team"].with_context(active_test=False).search([])
        mismatches = []
        for category in categories:
            compatible = teams.filtered(lambda team:
                category in team.pipeline_category_ids
                and (not category.company_id or category.company_id == team.company_id)
            )
            invalid = Domain("team_id", "not in", compatible.ids) | Domain("stage_id", "not in", category.stage_ids.ids)
            if category.company_id:
                invalid |= Domain("company_id", "!=", category.company_id.id)
            for team in compatible.filtered("company_id"):
                invalid |= Domain("team_id", "=", team.id) & Domain("company_id", "!=", team.company_id.id)
            mismatches.append(Domain("pipeline_category_id", "=", category.id) & invalid)
        return {
            "type": "ir.actions.act_window",
            "name": _("Pipeline Team Compatibility"),
            "res_model": "crm.lead",
            "view_mode": "list,form",
            "views": [
                (self.env.ref("kpability_sales_team_pipeline_categories.crm_lead_view_list_compatibility").id, "list"),
                (self.env.ref("kpability_sales_team_pipeline_categories.crm_lead_view_form_compatibility").id, "form"),
            ],
            "domain": list(Domain.OR(mismatches)),
            "context": {"active_test": False, "create": False, "edit": False, "delete": False},
        }
