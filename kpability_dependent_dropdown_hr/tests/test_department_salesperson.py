from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestDepartmentSalesperson(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a, cls.company_b = cls.env["res.company"].create([
            {"name": "DDF HR A"}, {"name": "DDF HR B"},
        ])
        cls.env = cls.env(context={
            **cls.env.context, "allowed_company_ids": [cls.company_a.id, cls.company_b.id],
            "mail_create_nolog": True, "mail_notrack": True,
        })
        cls.department, cls.other_department, cls.child_department, cls.department_b = cls.env[
            "hr.department"
        ].create([
            {"name": "Configured Commercial", "company_id": cls.company_a.id},
            {"name": "Sales (not configured)", "company_id": cls.company_a.id},
            {"name": "Commercial child", "company_id": cls.company_a.id},
            {"name": "Configured Commercial B", "company_id": cls.company_b.id},
        ])
        cls.child_department.parent_id = cls.department
        users = []
        for suffix in ("eligible", "other", "child", "archived_employee", "no_employee", "tenant_b"):
            company = cls.company_b if suffix == "tenant_b" else cls.company_a
            users.append(new_test_user(
                cls.env, login=f"ddf_hr_{suffix}", groups="sales_team.group_sale_salesman",
                company_id=company.id, company_ids=[Command.set(company.ids)],
            ))
        cls.eligible, cls.other, cls.child, cls.archived_employee_user, cls.no_employee, cls.tenant_b = users
        cls.employees = cls.env["hr.employee"].create([
            {"name": user.name, "user_id": user.id, "company_id": company.id,
             "department_id": department.id}
            for user, department, company in (
                (cls.eligible, cls.department, cls.company_a),
                (cls.other, cls.other_department, cls.company_a),
                (cls.child, cls.child_department, cls.company_a),
                (cls.archived_employee_user, cls.department, cls.company_a),
                (cls.tenant_b, cls.department_b, cls.company_b),
            )
        ])
        cls.employees[3].active = False
        cls.Filters = cls.env["dropdown.filters"]
        cls.crm_rule, cls.contacts_rule = cls.Filters.create([
            {"s_name": "DDF HR CRM", "company_id": cls.company_a.id, "active": True,
             "department_id": cls.department.id,
             "adapter_id": cls.env.ref("kpability_dependent_dropdown_hr.adapter_crm_sales_department").id},
            {"s_name": "DDF HR Contacts", "company_id": cls.company_a.id, "active": True,
             "department_id": cls.department.id,
             "adapter_id": cls.env.ref("kpability_dependent_dropdown_hr.adapter_contacts_sales_department").id},
        ])

    def _draft(self, model="crm.lead", user=None):
        return self.env[model].with_user(user or self.eligible).with_context(
            allowed_company_ids=self.company_a.ids,
        ).new({"name": "DDF HR Draft", "company_id": self.company_a.id, "user_id": False})

    def _choices(self, draft):
        # Public employees are a native SQL view. Model the completed HR RPC's flush
        # before reading it in a separate selector request; no eligibility cache exists.
        self.env.flush_all()
        return draft.env["res.users"].search(
            draft.env["dropdown.filters"]._get_domain(draft, "user_id"),
        )

    def test_exact_department_and_public_mapping_without_private_hr_access(self):
        self.assertFalse(self.env["hr.employee"].with_user(self.eligible).with_context(
            allowed_company_ids=self.company_a.ids,
        ).has_access("read"))
        self.assertTrue(self.env["hr.employee.public"].with_user(self.eligible).with_context(
            allowed_company_ids=self.company_a.ids,
        ).has_access("read"))
        for model in ("crm.lead", "res.partner"):
            self.assertEqual(self._choices(self._draft(model)), self.eligible)

    def test_department_is_reference_not_name_or_descendant(self):
        self.assertNotIn(self.other, self._choices(self._draft()))
        self.assertNotIn(self.child, self._choices(self._draft()))
        self.department.name = "Renamed configuration"
        self.assertEqual(self._choices(self._draft()), self.eligible)
        self.crm_rule.department_id = self.other_department
        self.assertEqual(self._choices(self._draft()), self.other)

    def test_inactive_employee_and_missing_employee_are_excluded(self):
        choices = self._choices(self._draft())
        self.assertNotIn(self.archived_employee_user, choices)
        self.assertNotIn(self.no_employee, choices)
        self.employees[0].active = False
        self.assertFalse(self._choices(self._draft()))

    def test_membership_change_is_not_cached(self):
        self.assertEqual(self._choices(self._draft()), self.eligible)
        self.employees[0].department_id = self.other_department
        self.assertFalse(self._choices(self._draft()))

    def test_missing_mapping_cannot_activate_and_wrong_company_rejected(self):
        self.crm_rule.active = False
        self.crm_rule.department_id = False
        with self.assertRaises(ValidationError):
            self.crm_rule.active = True
        with self.assertRaises(ValidationError):
            self.contacts_rule.department_id = self.department_b

    def test_backend_invalid_salesperson_rejected_but_unchanged_legacy_allowed(self):
        Lead = self.env["crm.lead"]
        with self.assertRaises(ValidationError):
            Lead.create({"name": "Invalid DDF HR", "company_id": self.company_a.id,
                         "user_id": self.other.id})
        self.crm_rule.active = False
        legacy = Lead.create({"name": "Legacy DDF HR", "company_id": self.company_a.id,
                              "user_id": self.other.id})
        self.crm_rule.active = True
        legacy.write({"description": "Unrelated history"})
        self.assertEqual(legacy.user_id, self.other)
        legacy.user_id = self.eligible
        self.contacts_rule.active = False
        legacy_partner = self.env["res.partner"].create({
            "name": "Legacy DDF contact", "company_id": self.company_a.id,
            "user_id": self.other.id,
        })
        self.contacts_rule.active = True
        # Native company classification changes are not a salesperson reassignment.
        legacy_partner.write({"vat": "US444444444"})
        self.assertEqual(legacy_partner.user_id, self.other)

    def test_internal_user_cannot_change_department_configuration(self):
        with self.assertRaises(AccessError):
            self.crm_rule.with_user(self.eligible).write({"department_id": self.other_department.id})

    def test_company_context_not_current_user_employee_selects_mapping(self):
        self.assertNotIn(self.tenant_b, self._choices(self._draft()))
        self.Filters.create({
            "s_name": "DDF HR B", "active": True, "company_id": self.company_b.id,
            "department_id": self.department_b.id, "adapter_id": self.crm_rule.adapter_id.id,
        })
        draft = self.env["crm.lead"].new({
            "name": "DDF HR B draft", "company_id": self.company_b.id, "user_id": False,
        })
        self.assertEqual(self._choices(draft), self.tenant_b)
