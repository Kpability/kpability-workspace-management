from psycopg2.errors import UniqueViolation

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestStageRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env["res.company"].create({"name": "Stage Rules Other Company"})
        cls.stage, cls.second_stage = cls.env["crm.stage"].create([
            {"name": "Stage Rules Qualification"}, {"name": "Stage Rules Review"},
        ])
        cls.rule_model = cls.env["stage.rules"]
        cls.field_model = cls.env["stage.rules.field"]
        cls.deadline_field = cls.env.ref("kpability_stage_rules.field_date_deadline")
        cls.referral_field = cls.env.ref("kpability_stage_rules.field_referred")
        cls.manager = new_test_user(
            cls.env, login="stage_rules_test_manager", groups="sales_team.group_sale_manager",
        )
        cls.salesperson = new_test_user(
            cls.env, login="stage_rules_test_salesperson", groups="sales_team.group_sale_salesman",
        )
        cls.non_salesperson = new_test_user(cls.env, login="stage_rules_test_non_salesperson")

    def _values(self, **overrides):
        return {
            "s_name": "Closing date at qualification",
            "company_id": self.company.id,
            "stage_ids": [Command.set(self.stage.ids)],
            "target_field_ids": [Command.set(self.deadline_field.ids)],
            "e_required": "when",
            "s_required_domain": "[('priority', '=', '3')]",
            **overrides,
        }

    def _payload(self, user, **context):
        payload = self.env["crm.lead"].with_user(user).with_context(**context).get_stage_rules_for_form()
        return [rule for rule in payload if self.stage.id in rule["stage_ids"]]

    def test_multiselect_and_independent_domains(self):
        rule = self.rule_model.create(self._values(
            stage_ids=[Command.set((self.stage | self.second_stage).ids)],
            target_field_ids=[Command.set((self.deadline_field | self.referral_field).ids)],
            e_visibility="when", s_visibility_domain="[('campaign_id', '!=', False)]",
            e_enabled="when", s_enabled_domain="['|', ('priority', '=', '3'), ('tag_ids', 'in', [5])]",
        ))
        self.assertFalse(rule.active)
        self.assertFalse(self._payload(self.salesperson))
        rule.active = True
        [payload] = self._payload(self.salesperson)
        self.assertEqual(set(payload["stage_ids"]), {self.stage.id, self.second_stage.id})
        self.assertEqual(set(payload["field_names"]), {"date_deadline", "referred"})
        self.assertEqual(payload["behaviors"], {
            "visibility": {"mode": "when", "domain": [("campaign_id", "!=", False)]},
            "enabled": {"mode": "when", "domain": ["|", ("priority", "=", "3"), ("tag_ids", "in", [5])]},
            "required": {"mode": "when", "domain": [("priority", "=", "3")]},
        })

    def test_payload_applies_any_effective_group_and_enabled_company(self):
        self.salesperson.sudo().write({"company_ids": [Command.link(self.other_company.id)]})
        unrelated_group = self.env["res.groups"].create({"name": "Stage Rules Unrelated Group"})
        restricted_group = self.env.ref("sales_team.group_sale_salesman_all_leads")
        self.rule_model.create([
            self._values(active=True, group_ids=[Command.set((unrelated_group | restricted_group).ids)]),
            self._values(active=True, company_id=self.other_company.id),
        ])
        self.assertEqual(len(self._payload(self.manager)), 1, "Include implied groups")
        self.assertFalse(self._payload(self.salesperson, allowed_company_ids=[self.company.id]))
        [payload] = self._payload(self.salesperson, allowed_company_ids=[self.other_company.id])
        self.assertEqual(payload["company_id"], self.other_company.id)
        with self.assertRaises(AccessError):
            self._payload(self.salesperson, allowed_company_ids=[999_999_999])
        with self.assertRaises(AccessError):
            self._payload(self.non_salesperson)

    def test_manager_company_and_catalog_access(self):
        rule = self.rule_model.with_user(self.manager).create(self._values())
        self.assertTrue(rule)
        with self.assertRaises(AccessError):
            self.rule_model.with_user(self.salesperson).search([])
        with self.assertRaises(AccessError):
            self.field_model.with_user(self.salesperson).get_field_choices()
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            rule.with_user(self.salesperson).write({"active": True})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.rule_model.with_user(self.manager).create(self._values(company_id=self.other_company.id))

    def test_register_existing_or_custom_fields_not_schema(self):
        field_count = len(self.env["crm.lead"]._fields)
        managers = self.field_model.with_user(self.manager)
        self.assertIn("phone", managers.get_field_choices())
        phone = managers.create({"s_field_name": "phone"})
        self.assertTrue(phone.s_name)
        self.assertEqual(len(self.env["crm.lead"]._fields), field_count)
        for name in ("stage_id", "not_a_field", "calendar_event_ids"):
            with self.subTest(name=name), self.assertRaises(ValidationError), self.env.cr.savepoint():
                managers.create({"s_field_name": name})
        with self.assertRaises(ValidationError):
            phone.s_field_name = "email_from"
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            managers.create({"s_field_name": "phone"})

    def test_wrong_field_operators_and_unusable_rules_are_rejected(self):
        for overrides in (
            {"stage_ids": [Command.clear()]},
            {"target_field_ids": [Command.clear()]},
            {"e_visibility": "hidden"},
            {"e_enabled": "disabled"},
            {"e_visibility": "when", "s_visibility_domain": "[('date_deadline', '!=', False)]"},
            {"s_required_domain": "['|', ('priority', '=', '3')]"},
            {"s_required_domain": "[('campaign_id.name', '=', 'Example')]"},
            {"s_required_domain": "[('campaign_id', 'child_of', [1])]"},
            {"s_required_domain": "[('date_deadline', '>', 'today')]"},
            {"s_required_domain": "[('priority', '=', uid)]"},
            {"s_required_domain": "[]"},
            {"e_required": "inherit", "active": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises(ValidationError), self.env.cr.savepoint():
                    self.rule_model.create(self._values(**overrides))

    def test_each_unreadable_behavior_is_filtered_independently(self):
        rule = self.rule_model.create(self._values(
            e_visibility="when", s_visibility_domain="[('campaign_id', '!=', False)]",
        ))
        self.assertEqual(rule._form_payload({
            "date_deadline": {"type": "date"}, "priority": {"type": "selection"},
        })["behaviors"], {
            "required": {"mode": "when", "domain": [("priority", "=", "3")]},
        })
        self.assertIsNone(rule._form_payload({"priority": {"type": "selection"}}))

    def test_rules_are_not_backend_write_validations(self):
        self.rule_model.create(self._values(active=True))
        opportunity = self.env["crm.lead"].create({
            "name": "Stage Rules direct write", "type": "opportunity",
            "company_id": self.company.id, "stage_id": self.stage.id, "priority": "3",
        })
        opportunity.write({"date_deadline": False})
        self.assertFalse(opportunity.date_deadline)
