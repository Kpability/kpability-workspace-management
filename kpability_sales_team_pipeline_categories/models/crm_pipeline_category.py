from odoo import Command, _, api, fields, models
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
        copy=False,
        help="Teams allowed to use this category. Both this form and Sales Teams edit the same mapping; "
             "team-side protections for used history and company scope still apply. "
             "Company-specific categories only accept teams of that company; shared categories accept any team.",
    )
    s_can_edit_sales_teams = fields.Boolean(
        string="Can Edit Sales Teams",
        compute="_compute_s_can_edit_sales_teams",
    )

    @api.depends_context("uid")
    def _compute_s_can_edit_sales_teams(self):
        can_write = self.env.user.has_group("sales_team.group_sale_manager")
        for category in self:
            category.s_can_edit_sales_teams = can_write

    @api.model_create_multi
    def create(self, vals_list):
        team_commands = []
        clean_vals_list = []
        for vals in vals_list:
            vals = dict(vals)
            team_commands.append(vals.pop("sales_team_ids", None))
            clean_vals_list.append(vals)
        categories = super().create(clean_vals_list)
        for category, commands in zip(categories, team_commands):
            if commands:
                category._set_sales_team_ids(commands)
        return categories

    def write(self, vals):
        commands = vals.get("sales_team_ids")
        vals = dict(vals)
        vals.pop("sales_team_ids", None)
        result = super().write(vals)
        if commands:
            for category in self:
                category._set_sales_team_ids(commands)
        return result

    def _set_sales_team_ids(self, commands):
        """Apply category-side edits through the authoritative team field.

        The relation table is shared, but routing writes through ``crm.team``
        keeps its access checks, active-category check, company-scope constraint
        and all-history removal protection in force.
        """
        self.ensure_one()
        current = self.sales_team_ids.with_context(active_test=False)
        target = current
        for command in commands:
            code = command[0]
            if code == Command.LINK:
                target |= self.env["crm.team"].browse(command[1])
            elif code == Command.UNLINK:
                target -= self.env["crm.team"].browse(command[1])
            elif code == Command.SET:
                target = self.env["crm.team"].browse(command[2])
            elif code == Command.CLEAR:
                target = self.env["crm.team"]
            elif code == Command.CREATE:
                raise UserError(_("Create the sales team from Sales Teams, then map it here."))
            else:
                raise UserError(_("Unsupported sales-team mapping command."))
        added = target - current
        if added:
            added.write({"pipeline_category_ids": [Command.link(self.id)]})
        removed = current - target
        if removed:
            removed.write({"pipeline_category_ids": [Command.unlink(self.id)]})

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
