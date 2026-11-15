from unittest.mock import patch

from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestDropdownFilters(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a, cls.company_b = cls.env["res.company"].create([
            {"name": "DDF Core A"}, {"name": "DDF Core B"},
        ])
        cls.env = cls.env(context={
            **cls.env.context, "allowed_company_ids": [cls.company_a.id, cls.company_b.id],
        })
        cls.user = new_test_user(
            cls.env, login="ddf_core_user", company_id=cls.company_a.id,
            company_ids=[Command.set(cls.company_a.ids)],
        )

    def setUp(self):
        super().setUp()
        # This catalog exists only inside the test transaction and patched allow-list.
        original = type(self.env["dropdown.adapter"])._definitions

        def definitions(adapters):
            return {
                **original(adapters),
                "test_direct_partner": {
                    "model": "res.partner", "child": "parent_id", "parent": "id",
                    "inverse": "parent_id",
                },
            }

        self.binding_patch = patch.object(type(self.env["dropdown.adapter"]), "_definitions", definitions)
        self.binding_patch.start()
        self.addCleanup(self.binding_patch.stop)
        self.adapter = self.env["dropdown.adapter"].create({
            "s_name": "Test-only binding", "s_key": "test_direct_partner",
        })
        self.Filters = self.env["dropdown.filters"]

    def _rule(self, **values):
        return self.Filters.create({
            "s_name": "DDF Core", "company_id": self.company_a.id,
            "adapter_id": self.adapter.id, **values,
        })

    def test_configuration_defaults_inactive_and_round_trip(self):
        rule = self._rule()
        self.assertFalse(rule.active)
        rule.write({"active": True, "s_name": "Reviewed"})
        self.assertEqual(rule.s_name, "Reviewed")
        self.assertTrue(rule.active)
        rule.active = False
        rule.unlink()

    def test_unregistered_binding_rejected(self):
        with self.assertRaises(ValidationError):
            self.env["dropdown.adapter"].create({"s_name": "Unsafe", "s_key": "eval(anything)"})

    def test_duplicate_binding_company_rejected_including_archived(self):
        self._rule()
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"), self.cr.savepoint():
            self._rule()
        self._rule(company_id=self.company_b.id)

    def test_internal_can_read_but_not_manage_configuration_or_catalog(self):
        rule = self._rule()
        self.assertEqual(rule.with_user(self.user).with_context(
            allowed_company_ids=self.company_a.ids,
        ).s_name, "DDF Core")
        for action in (
            lambda: rule.with_user(self.user).with_context(allowed_company_ids=self.company_a.ids).write({"active": True}),
            lambda: rule.with_user(self.user).with_context(allowed_company_ids=self.company_a.ids).unlink(),
            lambda: self.Filters.with_user(self.user).with_context(allowed_company_ids=self.company_a.ids).create({
                "s_name": "Spoof", "company_id": self.company_a.id, "adapter_id": self.adapter.id,
            }),
            lambda: self.adapter.with_user(self.user).write({"s_key": "other"}),
        ):
            with self.assertRaises(AccessError):
                action()

    def test_configuration_is_company_scoped(self):
        own = self._rule()
        other = self._rule(company_id=self.company_b.id)
        visible = self.Filters.with_user(self.user).with_context(
            allowed_company_ids=self.company_a.ids, active_test=False,
        ).search([("id", "in", (own | other).ids)])
        self.assertEqual(visible.ids, own.ids)

    def test_disabled_rule_preserves_native_domain_even_with_active_test_false(self):
        self._rule()
        parent = self.env["res.partner"].create({"name": "DDF Core parent", "is_company": True})
        native = [("id", "=", parent.id)]
        domain = self.Filters.with_context(active_test=False)._get_domain(parent, "parent_id", native)
        self.assertEqual(self.env["res.partner"].search(domain), parent)

    def test_unsaved_parent_denies_choices_and_native_domain_cannot_broaden(self):
        self._rule(active=True)
        parent = self.env["res.partner"].new({
            "name": "DDF Draft", "company_id": self.company_a.id,
        })
        self.assertFalse(self.env["res.partner"].search(
            self.Filters._get_domain(parent, "parent_id"),
        ))
        saved = self.env["res.partner"].create({
            "name": "DDF Saved", "company_id": self.company_a.id,
        })
        child = self.env["res.partner"].create({"name": "DDF Child", "parent_id": saved.id})
        self.assertEqual(self.env["res.partner"].search(
            self.Filters._get_domain(saved, "parent_id"),
        ), child)
        self.assertFalse(self.env["res.partner"].search(
            self.Filters._get_domain(saved, "parent_id", [("id", "=", saved.id)]),
        ))
