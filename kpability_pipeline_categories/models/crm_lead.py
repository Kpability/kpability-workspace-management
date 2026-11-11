from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain


class CrmLead(models.Model):
    _inherit = "crm.lead"

    pipeline_category_id = fields.Many2one(
        "crm.pipeline.category",
        string="Pipeline Category",
        index=True,
        tracking=True,
        ondelete="restrict",
        check_company=True,
        domain="[('active', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
    )
    pipeline_category_stage_ids = fields.Many2many(
        related="pipeline_category_id.stage_ids",
        string="Category Stages",
    )
    stage_id = fields.Many2one(
        domain="['|', ('team_ids', '=', False), ('team_ids', 'in', team_id)] "
        "+ ([('id', 'in', pipeline_category_stage_ids)] if pipeline_category_id else [])",
    )

    @api.depends("pipeline_category_id")
    def _compute_stage_id(self):
        # Native initialization/team handling remains intact. A category-only
        # change must NOT silently move an existing record to another stage.
        return super()._compute_stage_id()

    @api.model_create_multi
    def create(self, vals_list):
        leads = super().create(vals_list)
        leads.pipeline_category_id._check_assignable()
        return leads

    def write(self, vals):
        category_id = vals.get("pipeline_category_id")
        if category_id and any(lead.pipeline_category_id.id != category_id for lead in self):
            self.env["crm.pipeline.category"].browse(category_id)._check_assignable()
        return super().write(vals)

    @api.constrains("pipeline_category_id", "stage_id", "team_id", "company_id")
    def _check_pipeline_category_consistency(self):
        for lead in self:
            category = lead.pipeline_category_id
            if not category:
                continue
            category.check_access("read")
            if category.company_id and category.company_id != lead.company_id:
                raise ValidationError(_("The pipeline category must be shared or belong to the opportunity's company."))
            if not lead.stage_id or lead.stage_id not in category.stage_ids:
                raise ValidationError(_(
                    "Choose a stage mapped to the selected pipeline category, or clear the category. "
                    "Your current stage will not be changed automatically."
                ))
            if lead.stage_id.team_ids and lead.team_id not in lead.stage_id.team_ids:
                raise ValidationError(_("Choose a category stage available to this opportunity's sales team."))

    def _stage_find(self, team_id=False, domain=None, order="sequence, id", limit=1):
        # Singleton initialization and category/team buckets used by Won both
        # narrow native lookup. Never use UI context to override saved records.
        if self and all(lead.pipeline_category_id for lead in self):
            stage_ids = self.pipeline_category_id.stage_ids.ids
            domain = Domain(domain or []) & Domain("id", "in", stage_ids)
        return super()._stage_find(team_id=team_id, domain=domain, order=order, limit=limit)

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        visible_stages = super()._read_group_stage_ids(stages, domain)
        category_id = self.env.context.get("pipeline_category_scope_id")
        if not category_id:
            return visible_stages
        category = self.env["crm.pipeline.category"].browse(category_id).exists()
        if not category:
            raise UserError(_("This pipeline category no longer exists. Reopen Pipeline Categories."))
        category.check_access("read")
        return visible_stages & category.stage_ids

    def action_set_won(self):
        categorized = self.filtered("pipeline_category_id")
        uncategorized = self - categorized
        buckets = categorized.grouped(lambda lead: (lead.pipeline_category_id.id, lead.team_id.id))
        # Validate every bucket BEFORE changing any record in a bulk action.
        for leads in buckets.values():
            if not leads._stage_find(domain=[("is_won", "=", True)]):
                raise UserError(_(
                    "No Won stage is available for the selected category and sales team. "
                    "Ask a Sales Manager to map a compatible Won stage."
                ))
        if uncategorized:
            super(CrmLead, uncategorized).action_set_won()
        for leads in buckets.values():
            super(CrmLead, leads).action_set_won()
        return True

    def _merge_opportunity(self, user_id=False, team_id=False, auto_unlink=True, max_length=5):
        if len({lead.pipeline_category_id.id for lead in self}) > 1:
            raise UserError(_(
                "Align the pipeline categories and stages before merging these CRM records. "
                "Categorized and uncategorized records cannot be merged silently."
            ))
        return super()._merge_opportunity(
            user_id=user_id, team_id=team_id, auto_unlink=auto_unlink, max_length=max_length,
        )

    def _merge_get_fields(self):
        return super()._merge_get_fields() + ["pipeline_category_id"]
