from psycopg2.errors import UniqueViolation

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestStageRules(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env["res.company"].create({"name": "Stage Rules Other Company"})
        cls.stage = cls.env["crm.stage"].create({"name": "Stage Rules Qualification"})
        cls.rule_model = cls.env["stage.rules"]
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
            "stage_id": self.stage.id,
            "e_target_field": "date_deadline",
            "e_required": "when",
            "e_condition_field": "priority",
            "e_operator": "equals",
            "e_priority": "3",
            **overrides,
        }

    def _payload(self, user, **context):
        payload = self.env["crm.lead"].with_user(user).with_context(**context).get_stage_rules_for_form()
        return [rule for rule in payload if rule["stage_id"] == self.stage.id]

    def test_inactive_and_typed_payload(self):
        rule = self.rule_model.create(self._values())
        self.assertFalse(rule.active)
        self.assertFalse(self._payload(self.salesperson))
        rule.active = True
        [payload] = self._payload(self.salesperson)
        self.assertEqual(payload, {
            "company_id": self.company.id,
            "stage_id": self.stage.id,
            "field_name": "date_deadline",
            "required": "when",
            "enabled": "inherit",
            "visibility": "inherit",
            "condition": {"field_name": "priority", "operator": "equals", "value": "3"},
        })

    def test_payload_applies_group_and_active_company(self):
        self.salesperson.sudo().write({"company_ids": [(4, self.other_company.id)]})
        restricted_group = self.env.ref("sales_team.group_sale_salesman_all_leads")
        self.rule_model.create([
            self._values(active=True, group_id=restricted_group.id),
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

    def test_manager_company_and_salesperson_configuration_access(self):
        rule = self.rule_model.with_user(self.manager).create(self._values())
        self.assertTrue(rule)
        with self.assertRaises(AccessError):
            self.rule_model.with_user(self.salesperson).search([])
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            rule.with_user(self.salesperson).write({"active": True})
        with self.assertRaises(AccessError), self.env.cr.savepoint():
            self.rule_model.with_user(self.manager).create(self._values(company_id=self.other_company.id))
        self.assertFalse(self.rule_model.with_user(self.manager).search([
            ("company_id", "=", self.other_company.id),
        ]))

    def test_invalid_rules_are_rejected(self):
        for overrides in (
            {"e_visibility": "hidden"},
            {"e_enabled": "disabled"},
            {"e_enabled": "when", "e_required": "always"},
            {"e_target_field": "priority"},
            {"e_condition_field": "date_deadline", "e_operator": "is_set"},
            {"e_condition_field": "campaign_id", "e_operator": "equals"},
            {"e_priority": False},
            {"e_required": "inherit", "active": True},
        ):
            with self.subTest(overrides=overrides):
                with self.assertRaises((ValidationError, ValueError)), self.env.cr.savepoint():
                    self.rule_model.create(self._values(**overrides))

    def test_unique_active_scope_allows_inactive_drafts_and_role_rules(self):
        self.rule_model.create(self._values(active=True))
        draft = self.rule_model.create(self._values())
        with self.assertRaises(UniqueViolation), self.env.cr.savepoint():
            draft.write({"active": True})
            draft.flush_recordset()
        draft.write({
            "active": True, "group_id": self.env.ref("sales_team.group_sale_manager").id,
        })
        self.assertTrue(draft.active)

    def test_rules_are_not_backend_write_validations(self):
        self.rule_model.create(self._values(active=True))
        opportunity = self.env["crm.lead"].create({
            "name": "Stage Rules direct write", "type": "opportunity",
            "company_id": self.company.id, "stage_id": self.stage.id, "priority": "3",
        })
        opportunity.write({"date_deadline": False})
        self.assertFalse(opportunity.date_deadline)
