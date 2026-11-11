from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain


class CrmStage(models.Model):
    _inherit = "crm.stage"

    pipeline_category_ids = fields.Many2many(
        "crm.pipeline.category",
        "crm_pipeline_category_stage_rel",
        "stage_id",
        "category_id",
        string="Pipeline Categories",
        readonly=True,
        copy=False,
        help="Manage mappings from Pipeline Categories. Stage ordering is shared across all categories.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if any("pipeline_category_ids" in vals for vals in vals_list):
            raise UserError(_("Manage stage mappings from Pipeline Categories, not from stages."))
        return super().create(vals_list)

    def write(self, vals):
        if "pipeline_category_ids" in vals:
            raise UserError(_("Manage stage mappings from Pipeline Categories, not from stages."))
        return super().write(vals)

    @api.constrains("team_ids")
    def _check_categorized_lead_teams(self):
        # See the existence-only security rationale in category._check_pipeline_usage.
        leads = self.env["crm.lead"].sudo().with_context(active_test=False)
        for stage in self:
            if stage.team_ids and leads.search_count(
                Domain("stage_id", "=", stage.id)
                & Domain("pipeline_category_id", "!=", False)
                & Domain("team_id", "not in", stage.team_ids.ids),
                limit=1,
            ):
                raise ValidationError(_(
                    "These sales-team restrictions would invalidate categorized CRM records, including archived records. "
                    "Reassign those records explicitly before changing this stage."
                ))
