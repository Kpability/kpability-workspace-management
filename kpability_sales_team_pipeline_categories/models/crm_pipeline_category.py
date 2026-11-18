from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class CrmPipelineCategory(models.Model):
    _inherit = "crm.pipeline.category"

    sales_team_ids = fields.Many2many(
        "crm.team",
        "crm_team_pipeline_category_rel",
        "category_id",
        "team_id",
        string="Sales Teams",
        context={"active_test": False},
        readonly=True,
        copy=False,
        help="Read-only inverse. Manage category eligibility from Sales Teams; archiving preserves these mappings.",
    )

    @api.model_create_multi
    def create(self, vals_list):
        if any("sales_team_ids" in vals for vals in vals_list):
            raise UserError(_("Manage pipeline category mappings from Sales Teams, not from categories."))
        return super().create(vals_list)

    def write(self, vals):
        if "sales_team_ids" in vals:
            raise UserError(_("Manage pipeline category mappings from Sales Teams, not from categories."))
        return super().write(vals)

    @api.constrains("company_id")
    def _check_sales_team_company_scope(self):
        # A shared category can be linked to teams outside the editor's selected
        # companies. Only test existence; never expose hidden teams to the editor.
        teams = self.env["crm.team"].sudo().with_context(active_test=False)
        for category in self.filtered("company_id"):
            if teams.search_count([
                ("pipeline_category_ids", "in", category.ids),
                ("company_id", "!=", category.company_id.id),
            ], limit=1):
                raise ValidationError(_(
                    "This company scope is incompatible with existing sales-team mappings, including archived teams. "
                    "Keep the category shared, or explicitly change those mappings first."
                ))
