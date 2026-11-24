from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError, ValidationError

# Context values survive internal ``with_context`` calls but cannot be sent over
# JSON/XML-RPC, so a user-supplied True value cannot defer the scope check.
_DEFER_COMPANY_SCOPE = object()


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

    @api.model
    def _default_sales_team_commands(self):
        value = self.default_get(["sales_team_ids"]).get("sales_team_ids")
        return self._normalize_sales_team_commands(value) if value else None

    @api.model
    def _normalize_sales_team_commands(self, commands):
        if commands is None:
            return []
        if isinstance(commands, models.BaseModel):
            return [Command.set(commands.ids)]
        if commands is False or not commands:
            return [Command.clear()]
        if isinstance(commands[0], int):
            if commands[0] in {Command.CREATE, Command.UPDATE, Command.DELETE,
                               Command.UNLINK, Command.LINK, Command.CLEAR, Command.SET}:
                return [commands]
            if all(isinstance(command, int) for command in commands):
                return [Command.set(commands)]
        return list(commands)

    @api.model_create_multi
    def create(self, vals_list):
        prepared = []
        default_commands = None
        for vals in vals_list:
            vals = dict(vals)
            if "sales_team_ids" in vals:
                commands = self._normalize_sales_team_commands(vals.pop("sales_team_ids"))
            else:
                if default_commands is None:
                    default_commands = self._default_sales_team_commands()
                commands = default_commands
            # Resolve defaults here so they take the same guarded team-side path
            # as explicit values. The clear sentinel prevents base create from
            # writing the raw relation default a second time.
            vals["sales_team_ids"] = [Command.clear()]
            prepared.append((vals, commands))
        categories = super().create([vals for vals, _commands in prepared])
        for category, (_vals, commands) in zip(categories, prepared):
            if commands is not None:
                category._set_sales_team_ids(commands)
            category._check_sales_team_company_scope()
        return categories

    def write(self, vals):
        commands = vals.get("sales_team_ids") if "sales_team_ids" in vals else None
        vals = dict(vals)
        vals.pop("sales_team_ids", None)
        company_change = "company_id" in vals
        # A simultaneous company scope and mapping change is validated against
        # its final state, not the old relation rows that are about to be replaced.
        defer_scope = company_change and commands is not None
        if defer_scope:
            self = self.with_context(kpability_stpc_defer_company_scope=_DEFER_COMPANY_SCOPE)
        result = super().write(vals)
        if commands is not None:
            commands = self._normalize_sales_team_commands(commands)
            for category in self:
                category._set_sales_team_ids(commands)
        if company_change:
            self.with_context(kpability_stpc_defer_company_scope=False)._check_sales_team_company_scope()
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
        if self.env.context.get("kpability_stpc_defer_company_scope") is _DEFER_COMPANY_SCOPE:
            return
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
