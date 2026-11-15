from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, ValidationError
from odoo.tests import Form, TransactionCase, new_test_user, tagged


@tagged("post_install", "-at_install")
class TestCompanyContact(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a, cls.company_b = cls.env["res.company"].create([
            {"name": "DDF Tenant A"}, {"name": "DDF Tenant B"},
        ])
        cls.env = cls.env(context={
            **cls.env.context, "allowed_company_ids": [cls.company_a.id, cls.company_b.id],
            "mail_create_nolog": True, "mail_notrack": True,
        })
        cls.Partner = cls.env["res.partner"]
        cls.Lead = cls.env["crm.lead"]
        cls.Filters = cls.env["dropdown.filters"]
        cls.customer_a, cls.customer_b = cls.Partner.create([
            {"name": "DDF Customer A", "vat": "US123456789", "company_id": cls.company_a.id},
            {"name": "DDF Customer B", "vat": "US987654321", "company_id": cls.company_a.id},
        ])
        cls.person_a, cls.person_b, cls.archived = cls.Partner.create([
            {"name": "DDF Person A", "parent_id": cls.customer_a.id, "company_id": cls.company_a.id},
            {"name": "DDF Person B", "parent_id": cls.customer_b.id, "company_id": cls.company_a.id},
            {"name": "DDF Archived", "parent_id": cls.customer_a.id,
             "company_id": cls.company_a.id, "active": False},
        ])
        cls.grandchild = cls.Partner.create({
            "name": "DDF Grandchild", "parent_id": cls.person_a.id,
        })
        cls.sales = new_test_user(
            cls.env, login="ddf_contacts_sales", groups="sales_team.group_sale_salesman",
            company_id=cls.company_a.id, company_ids=[Command.set(cls.company_a.ids)],
        )
        cls.crm_rule, cls.contacts_rule = cls.Filters.create([
            {"s_name": "DDF CRM A", "company_id": cls.company_a.id, "active": True,
             "adapter_id": cls.env.ref(
                 "kpability_dependent_dropdown_crm_contacts.adapter_crm_customer_contact",
             ).id},
            {"s_name": "DDF Contacts A", "company_id": cls.company_a.id, "active": True,
             "adapter_id": cls.env.ref(
                 "kpability_dependent_dropdown_crm_contacts.adapter_contacts_primary_contact",
             ).id},
        ])

    def _lead(self, **values):
        return self.Lead.create({
            "name": "DDF Opportunity", "type": "opportunity", "company_id": self.company_a.id,
            "user_id": False, "customer_company_id": self.customer_a.id,
            "partner_id": self.person_a.id, **values,
        })

    def _choices(self, record, field="partner_id"):
        return record.env[record._fields[field].comodel_name].search(
            record.env["dropdown.filters"]._get_domain(record, field),
        )

    def test_exact_direct_active_individuals_only(self):
        lead = self._lead()
        self.assertEqual(self._choices(lead), self.person_a)
        self.assertEqual(self._choices(lead.with_context(active_test=False)), self.person_a)
        self.assertEqual(self._choices(lead.with_user(self.sales).with_context(
            allowed_company_ids=self.company_a.ids,
        )), self.person_a)

    def test_missing_and_empty_parent_have_no_choices(self):
        lead = self._lead(partner_id=False, customer_company_id=False)
        self.assertFalse(self._choices(lead))
        self.assertIn("saved customer company", lead.s_dropdown_contact_hint)
        self.person_b.active = False
        lead.customer_company_id = self.customer_b
        self.assertFalse(self._choices(lead))
        self.assertIn("No eligible", lead.s_dropdown_contact_hint)

    def test_draft_parent_changes_keep_child_and_unrelated_draft(self):
        saved = self._lead()
        with Form(saved) as form:
            form.name = "Unrelated draft"
            form.customer_company_id = self.customer_b
            self.assertEqual(form.partner_id, self.person_a)
            self.assertIn("no longer matches", form.s_dropdown_contact_hint)
            form.partner_id = self.person_b
        self.assertEqual(saved.name, "Unrelated draft")
        self.assertEqual(saved.partner_id, self.person_b)

    def test_create_and_write_reject_invalid_relationship_without_context_bypass(self):
        for context in ({}, {"active_test": False}, {"skip_dropdown_validation": True}):
            with self.assertRaises(ValidationError):
                self.Lead.with_context(**context).create({
                    "name": "DDF Invalid", "company_id": self.company_a.id, "user_id": False,
                    "customer_company_id": self.customer_b.id, "partner_id": self.person_a.id,
                })
        lead = self._lead()
        with self.assertRaises(ValidationError):
            lead.write({"customer_company_id": self.customer_b.id})
        # Tests catch exceptions without ending the transaction; restore the draft explicitly.
        lead.invalidate_recordset()

    def test_explicit_clear_and_atomic_parent_child_change_work(self):
        lead = self._lead()
        lead.write({"customer_company_id": self.customer_b.id, "partner_id": self.person_b.id})
        self.assertEqual(lead.partner_id, self.person_b)
        lead.write({"customer_company_id": False, "partner_id": False})
        self.assertFalse(lead.partner_id)

    def test_legacy_unrelated_edit_and_deactivation_do_not_rewrite_history(self):
        self.crm_rule.active = False
        lead = self._lead(customer_company_id=self.customer_b.id)
        native_text = lead.partner_name
        self.crm_rule.active = True
        lead.write({"description": "Allowed legacy note"})
        self.assertEqual(lead.partner_id, self.person_a)
        self.assertEqual(lead.partner_name, native_text)
        self.assertIn("no longer matches", lead.s_dropdown_contact_hint)
        self.crm_rule.active = False
        lead.write({"name": "Still preserved"})
        self.assertEqual(lead.partner_id, self.person_a)

    def test_contacts_reuse_and_unsaved_company(self):
        self.customer_a.primary_contact_id = self.person_a
        self.assertEqual(self._choices(self.customer_a, "primary_contact_id"), self.person_a)
        draft = self.Partner.new({
            "name": "DDF Unsaved company", "vat": "US111111111", "company_id": self.company_a.id,
        })
        self.assertFalse(self._choices(draft, "primary_contact_id"))
        persisted_draft = self.Partner.new(
            self.customer_a.copy_data()[0], origin=self.customer_a,
        )
        self.assertEqual(self._choices(persisted_draft, "primary_contact_id"), self.person_a)
        with self.assertRaises(ValidationError):
            self.customer_a.primary_contact_id = self.person_b

    def test_second_configuration_company_and_existing_record_preservation(self):
        customer = self.Partner.create({
            "name": "DDF Tenant B customer", "vat": "US222222222", "company_id": self.company_b.id,
        })
        child = self.Partner.create({
            "name": "DDF Tenant B person", "parent_id": customer.id, "company_id": self.company_b.id,
        })
        lead = self._lead(company_id=self.company_b.id, customer_company_id=customer.id, partner_id=child.id)
        snapshot = (lead.partner_id.id, lead.customer_company_id.id, lead.write_date)
        self.crm_rule.copy({"s_name": "DDF CRM B", "company_id": self.company_b.id})
        self.assertEqual(self._choices(lead), child)
        self.assertEqual(snapshot, (lead.partner_id.id, lead.customer_company_id.id, lead.write_date))

    def test_native_domain_and_company_rules_intersect(self):
        lead = self._lead()
        self.assertFalse(self.Partner.search(
            self.Filters._get_domain(lead, "partner_id", [("id", "=", self.person_b.id)]),
        ))
        secret_company = self.Partner.create({
            "name": "DDF Inaccessible customer", "vat": "US333333333", "company_id": self.company_b.id,
        })
        secret_child = self.Partner.create({
            "name": "DDF Inaccessible child", "parent_id": secret_company.id,
        })
        draft = self.Lead.with_user(self.sales).with_context(
            allowed_company_ids=self.company_a.ids,
        ).new({
            "name": "DDF Draft", "company_id": self.company_a.id,
            "customer_company_id": secret_company.id,
        })
        self.assertNotIn(secret_child, self._choices(draft))

    def test_filtered_autocomplete_and_search_more_use_same_domain(self):
        lead = self._lead()
        domain = list(self.Filters._get_domain(lead, "partner_id"))
        autocomplete = self.Partner.name_search(name="DDF", domain=domain, limit=8)
        search_more = self.Partner.search(domain, offset=0, limit=80)
        self.assertEqual([item[0] for item in autocomplete], self.person_a.ids)
        self.assertEqual(search_more, self.person_a)

    def test_views_preserve_native_widgets_contexts_and_disable_creation(self):
        arch = etree.fromstring(self.Lead.get_view(
            self.env.ref("crm.crm_lead_view_form").id, "form",
        )["arch"])
        selectors = arch.xpath("//group[@name='lead_partner']/field[@name='partner_id']")
        self.assertEqual(len(selectors), 2)
        for selector in selectors:
            self.assertEqual(selector.get("domain"), "j_dropdown_contact_domain")
            self.assertEqual(selector.get("widget"), "res_partner_many2one")
            self.assertIn("'no_create': True", selector.get("options"))
            self.assertIn("default_email", selector.get("context"))

    def test_sales_user_cannot_activate_rule(self):
        with self.assertRaises(AccessError):
            self.crm_rule.with_user(self.sales).write({"active": False})
