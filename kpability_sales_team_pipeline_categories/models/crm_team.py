from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class CrmTeam(models.Model):
    _inherit = "crm.team"

    pipeline_category_ids = fields.Many2many(
        "crm.pipeline.category",
        "crm_team_pipeline_category_rel",
        "team_id",
        "category_id",
        string="Pipeline Categories",
        context={"active_test": False},
        domain="[('active', '=', True), ('company_id', 'in', [False, company_id])]",
        copy=False,
        help="Only mapped categories may be assigned to this team. An empty mapping allows no new categorized assignments. "
             "Companyless teams may use shared categories only. Existing CRM history is never reclassified automatically.",
    )

    @api.constrains("pipeline_category_ids", "company_id")
    def _check_pipeline_category_scope(self):
        for team in self:
            categories = team.pipeline_category_ids
            categories.check_access("read")
            if any(category.company_id and category.company_id != team.company_id for category in categories):
                raise ValidationError(_(
                    "Map only shared categories or categories belonging to the sales team's company. "
                    "A companyless team can map shared categories only."
                ))

    @api.model_create_multi
    def create(self, vals_list):
        teams = super().create(vals_list)
        teams._check_pipeline_category_scope()
        teams.pipeline_category_ids._check_assignable()
        return teams

    def write(self, vals):
        if not {"pipeline_category_ids", "company_id"}.intersection(vals):
            return super().write(vals)
        self.check_access("write")
        previous = {team.id: (team.pipeline_category_ids, team.company_id) for team in self}
        result = super().write(vals)
        # Existence-only elevation protects hidden/archived history. Never return
        # business records, names, identifiers or counts through this check.
        leads = self.env["crm.lead"].sudo().with_context(active_test=False)
        for team in self:
            old_categories, old_company = previous[team.id]
            (team.pipeline_category_ids - old_categories)._check_assignable()
            removed = old_categories - team.pipeline_category_ids
            invalid = bool(removed) and leads.search_count([
                ("team_id", "=", team.id), ("pipeline_category_id", "in", removed.ids),
            ], limit=1)
            if team.company_id != old_company and team.company_id:
                invalid = invalid or leads.search_count([
                    ("team_id", "=", team.id), ("pipeline_category_id", "!=", False),
                    ("company_id", "!=", team.company_id.id),
                ], limit=1)
            if invalid:
                raise ValidationError(_(
                    "This change would invalidate existing categorized CRM records, including archived, Won and Lost records. "
                    "Keep their team/category mappings and company scope, or explicitly reclassify the records first."
                ))
        return result

    @api.ondelete(at_uninstall=False)
    def _unlink_except_categorized_history(self):
        if self.env["crm.lead"].sudo().with_context(active_test=False).search_count([
            ("team_id", "in", self.ids), ("pipeline_category_id", "!=", False),
        ], limit=1):
            raise UserError(_(
                "This sales team is used by categorized CRM records, including historical records. "
                "Archive the team, or explicitly reclassify its records before deleting it."
            ))
