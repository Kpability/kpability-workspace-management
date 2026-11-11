from markupsafe import Markup

from odoo import _, api, models
from odoo.exceptions import AccessError


class ResUsers(models.Model):
    _inherit = "res.users"

    @api.model
    def action_workspace_user_roles(self):
        if not self.env.su and not self.env.user.has_group(
                "base.group_system"
        ):
            raise AccessError(_("Administrator access is required."))

        scope = (
                self.env["ir.config_parameter"]
                .sudo()
                .get_str("workspace_management.role_scope", "")
                or ""
        ).strip()

        categories = self.env["ir.module.category"].search(
            [("name", "=", scope)],
            limit=2,
        ) if scope else self.env["ir.module.category"]

        columns = []

        if len(categories) == 1:
            privileges = self.env["res.groups.privilege"].search(
                [("category_id", "=", categories.id)],
                order="sequence, name, id",
            )

            hierarchy = (
                self.env["res.groups"]._get_view_group_hierarchy()
            )

            for privilege in privileges:
                group_ids = hierarchy["privileges"][
                    privilege.id
                ]["group_ids"]

                columns.append({
                    "id": privilege.id,
                    "label": privilege.name,
                    "emptyLabel": privilege.placeholder or _("No"),
                    "groups": [
                        {
                            "id": group_id,
                            "name": hierarchy["groups"][group_id]["name"],
                            "impliers": hierarchy["groups"][group_id][
                                "all_implied_by_ids"
                            ],
                        }
                        for group_id in group_ids
                    ],
                })

        action = self.env["ir.actions.actions"]._for_xml_id(
            "workspace_management.action_workspace_user_roles"
        )

        action["context"] = {
            "workspace_role_columns": columns,
            "search_default_internal_users": 1,
        }

        action["domain"] = (
            [("share", "=", False)]
            if columns
            else [("id", "=", False)]
        )

        message = (
            _("No internal users to display.")
            if columns
            else _(
                "Configure a unique role category with privileges "
                "in workspace_management.role_scope."
            )
        )

        action["help"] = str(
            Markup(
                '<p class="o_view_nocontent_smiling_face">%s</p>'
            ) % message
        )

        return action