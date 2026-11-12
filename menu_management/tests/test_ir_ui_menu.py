from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged("post_install", "-at_install")
class TestMenuManagement(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.menus = cls.env["ir.ui.menu"]
        category = cls.env["ir.module.category"].create({"name": "Menu Test Scope"})
        cls.env["ir.config_parameter"].set_str("workspace_management.role_scope", category.name)
        privilege = cls.env["res.groups.privilege"].create({
            "name": "Test Roles", "category_id": category.id,
        })
        cls.role = cls.env["res.groups"].create({
            "name": "Test Agent", "privilege_id": privilege.id,
        })
        cls.manager = cls.env["res.groups"].create({
            "name": "Test Manager", "privilege_id": privilege.id,
            "implied_ids": [fields.Command.link(cls.role.id)],
        })
        cls.outside_role = cls.env["res.groups"].create({"name": "Outside Scope"})
        cls.user = new_test_user(
            cls.env, login="menu_unit_test_user",
            group_ids=(cls.manager | cls.env.ref("base.group_user")).ids,
        )
        action = cls.env["ir.actions.client"].create({
            "name": "Test App", "tag": "display_notification",
        })
        cls.root = cls.menus.create({
            "name": "Test App", "action": f"ir.actions.client,{action.id}",
            "group_ids": [fields.Command.link(cls.role.id)],
        })
        cls.child = cls.menus.create({
            "name": "Test Submenu", "parent_id": cls.root.id,
            "action": f"ir.actions.client,{action.id}",
        })

    def test_workspace_roles(self):
        roles = self.menus._workspace_roles()
        self.assertEqual(set(roles.ids), {self.role.id, self.manager.id})
        self.assertNotIn(self.outside_role, roles)

    def test_workspace_menu_data(self):
        data = self.menus.workspace_menu_data()
        menu_ids = {menu["id"] for menu in data["menus"]}
        self.assertEqual({role["id"] for role in data["roles"]}, {self.role.id, self.manager.id})
        self.assertIn(self.root.id, menu_ids)
        self.assertNotIn(self.child.id, menu_ids)
        self.assertNotIn(self.env.ref("workspace_management.menu_workspace_management").id, menu_ids)

    def test_workspace_set_menu_group(self):
        self.root.workspace_set_menu_group(self.manager.id, False)
        self.assertIn(self.manager, self.root.workspace_hidden_group_ids)
        self.root.workspace_set_menu_group(self.manager.id, True)
        self.assertNotIn(self.manager, self.root.workspace_hidden_group_ids)

    def test_visible_menu_ids(self):
        menus = self.menus.with_user(self.user)
        app_ids = {self.root.id, self.child.id}
        self.assertTrue(app_ids <= menus._visible_menu_ids())
        self.root.workspace_set_menu_group(self.manager.id, False)
        self.assertFalse(app_ids & menus._visible_menu_ids())
        self.root.workspace_set_menu_group(self.manager.id, True)
        self.assertTrue(app_ids <= menus._visible_menu_ids())
