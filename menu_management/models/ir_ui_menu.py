from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrUiMenu(models.Model):
    _inherit = "ir.ui.menu"

    workspace_hidden_group_ids = fields.Many2many(
        "res.groups", string="Hidden Groups", groups="base.group_system",
    )

    def _workspace_roles(self):
        self.check_access("write")
        scope = self.env["ir.config_parameter"].sudo().get_str(
            "workspace_management.role_scope", ""
        ).strip()
        categories = self.env["ir.module.category"].search([("name", "=", scope)], limit=2)
        return self.env["res.groups"].search(
            [("privilege_id.category_id", "=", categories.id)],
            order="privilege_id, sequence desc, id",
        ) if scope and len(categories) == 1 else self.env["res.groups"]

    @api.model
    def workspace_menu_data(self):
        roles = self._workspace_roles()
        return {
            "roles": roles.read(["name", "all_implied_ids"]),
            "menus": self.search([
                ("parent_id", "=", False),
                ("id", "!=", self.env.ref("workspace_management.menu_workspace_management").id),
            ]).read(["name", "group_ids", "workspace_hidden_group_ids", "web_icon"]),
        }

    def workspace_set_menu_group(self, role_id, enabled):
        roles = self._workspace_roles()
        role = roles.filtered(lambda group: group.id == role_id)
        workspace = self.env.ref("workspace_management.menu_workspace_management")
        if not role or type(enabled) is not bool or any(menu.parent_id or menu == workspace for menu in self):
            raise ValidationError(_("Invalid menu selection."))
        for menu in self:
            values = {"workspace_hidden_group_ids": [
                fields.Command.unlink(role.id) if enabled else fields.Command.link(role.id),
            ]}
            if enabled and menu.group_ids and not menu.group_ids & role.all_implied_ids:
                values["group_ids"] = [fields.Command.link(role.id)]
            menu.write(values)
        return self.read(["group_ids", "workspace_hidden_group_ids"])

    @api.model
    @api.ormcache("frozenset(self.env.user._get_group_ids())", "debug")
    def _visible_menu_ids(self, debug=False):
        visible = super()._visible_menu_ids(debug)
        roles = self.sudo()._workspace_roles().filtered(
            lambda group: group.id in self.env.user._get_group_ids()
        )
        # Evaluate the assigned level, not the lower roles it implies.
        roles = roles.filtered(lambda group: not any(
            group != other and group in other.all_implied_ids for other in roles
        ))
        if not roles:
            return visible
        roots = self.sudo().search([
            ("parent_id", "=", False), ("id", "in", list(visible)),
            ("workspace_hidden_group_ids", "in", roles.ids),
        ])
        hidden = roots.filtered(lambda menu: not any(
            role not in menu.workspace_hidden_group_ids
            and (not menu.group_ids or bool(menu.group_ids & role.all_implied_ids))
            for role in roles
        ))
        descendants = self.sudo().search([("id", "child_of", hidden.ids)]) if hidden else self.browse()
        return frozenset(visible.difference(descendants.ids))
