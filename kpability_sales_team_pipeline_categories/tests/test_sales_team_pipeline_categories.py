from lxml import etree

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, new_test_user, tagged

from ..models.crm_lead import CrmLead


@tagged("post_install", "-at_install")
class TestSalesTeamPipelineCategories(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a, cls.company_b = cls.env["res.company"].create([
            {"name": "STPC Company A"}, {"name": "STPC Company B"},
        ])
        cls.env = cls.env(context={
            **cls.env.context, "allowed_company_ids": (cls.company_a | cls.company_b).ids,
            "mail_create_nolog": True, "mail_notrack": True,
        })
        cls.Lead = cls.env["crm.lead"]
        cls.Team = cls.env["crm.team"]
        cls.Category = cls.env["crm.pipeline.category"]
        cls.Stage = cls.env["crm.stage"]
        cls.manager = new_test_user(
            cls.env, login="stpc_manager", groups="sales_team.group_sale_manager,base.group_multi_company",
            company_id=cls.company_a.id, company_ids=[Command.set((cls.company_a | cls.company_b).ids)],
        )
        cls.sales = new_test_user(
            cls.env, login="stpc_sales", groups="sales_team.group_sale_salesman", company_id=cls.company_a.id,
        )
        cls.other_sales = new_test_user(
            cls.env, login="stpc_other_sales", groups="sales_team.group_sale_salesman", company_id=cls.company_a.id,
        )
        cls.stage_common, cls.stage_a, cls.stage_other, cls.won = cls.Stage.create([
            {"name": "STPC Intake", "sequence": -8000},
            {"name": "STPC Team A Review", "sequence": -7990},
            {"name": "STPC Alternative Review", "sequence": -7980},
            {"name": "STPC Won", "sequence": 9000, "is_won": True},
        ])
        cls.category_a, cls.category_other, cls.category_b, cls.category_shared = cls.Category.create([
            {"s_name": "STPC A", "company_id": cls.company_a.id,
             "stage_ids": [Command.set((cls.stage_common | cls.stage_a | cls.won).ids)]},
            {"s_name": "STPC Alternative", "company_id": cls.company_a.id,
             "stage_ids": [Command.set((cls.stage_common | cls.stage_other | cls.won).ids)]},
            {"s_name": "STPC B", "company_id": cls.company_b.id,
             "stage_ids": [Command.set((cls.stage_common | cls.won).ids)]},
            {"s_name": "STPC Shared", "company_id": False,
             "stage_ids": [Command.set((cls.stage_common | cls.stage_a | cls.won).ids)]},
        ])
        cls.team_a, cls.team_other, cls.team_b, cls.team_global, cls.team_empty = cls.Team.create([
            {"name": "STPC Alpha", "company_id": cls.company_a.id,
             "pipeline_category_ids": [Command.set((cls.category_a | cls.category_shared).ids)]},
            {"name": "STPC Alternative", "company_id": cls.company_a.id,
             "member_ids": [Command.link(cls.other_sales.id)],
             "pipeline_category_ids": [Command.set((cls.category_other | cls.category_shared).ids)]},
            {"name": "STPC Beta", "company_id": cls.company_b.id,
             "pipeline_category_ids": [Command.set((cls.category_b | cls.category_shared).ids)]},
            {"name": "STPC Global", "company_id": False,
             "pipeline_category_ids": [Command.link(cls.category_shared.id)]},
            {"name": "STPC Empty", "company_id": cls.company_a.id},
        ])
        cls.stage_a.team_ids = cls.team_a

    def _values(self, category, **overrides):
        values = {
            "name": "STPC Opportunity", "type": "opportunity", "user_id": False,
            "team_id": self.team_a.id, "company_id": self.company_a.id,
            "pipeline_category_id": category.id if category else False,
        }
        values.update(overrides)
        return values

    def _lead(self, category, **overrides):
        return self.Lead.create(self._values(category, **overrides))

    def _legacy(self, category, **overrides):
        # Emulate a pre-install record using only the already-approved base ORM.
        # Production has no context flag or public bypass for this invariant.
        return super(CrmLead, self.Lead).create([self._values(category, **overrides)])

    def test_stpc01_mapping_round_trip_and_inverse(self):
        self.assertEqual(self.category_a.sales_team_ids, self.team_a)
        self.assertEqual(set(self.category_shared.sales_team_ids.ids), {
            self.team_a.id, self.team_other.id, self.team_b.id, self.team_global.id,
        })
        self.team_other.with_user(self.manager).write({"pipeline_category_ids": [Command.link(self.category_a.id)]})
        self.env.invalidate_all()
        self.assertIn(self.team_other, self.category_a.sales_team_ids)
        self.team_other.write({"pipeline_category_ids": [Command.unlink(self.category_a.id)]})
        self.assertNotIn(self.team_other, self.category_a.sales_team_ids)

    def test_stpc01_inverse_is_protected_for_rpc_create_write_and_copy(self):
        for category in (self.category_shared, self.category_shared.sudo()):
            with self.assertRaises(UserError):
                category.write({"sales_team_ids": [Command.clear()]})
        with self.assertRaises(UserError):
            self.Category.create({"s_name": "STPC Spoof", "sales_team_ids": [Command.link(self.team_a.id)]})
        copied = self.category_a.copy({"s_name": "STPC Category Copy"})
        self.assertFalse(copied.sales_team_ids)
        self.assertFalse(self.team_a.copy({"name": "STPC Team Copy"}).pipeline_category_ids)

    def test_stpc02_categories_follow_draft_team_and_company(self):
        draft = self.Lead.new(self._values(False))
        self.assertEqual(draft.pipeline_team_category_ids._origin, self.team_a.pipeline_category_ids)
        draft.team_id = self.team_other
        self.assertEqual(draft.pipeline_team_category_ids._origin, self.team_other.pipeline_category_ids)
        self.assertFalse(draft.pipeline_category_id)
        self.assertFalse(self.Lead.new(self._values(False, team_id=False)).pipeline_team_category_ids)
        self.assertIn("pipeline_team_category_ids", self.Lead._fields["pipeline_category_id"].domain)

    def test_stpc02_new_archived_mapping_rejected(self):
        self.category_a.active = False
        with self.assertRaises(ValidationError):
            self.team_other.write({"pipeline_category_ids": [Command.link(self.category_a.id)]})
        with self.assertRaises(ValidationError):
            self.Team.create({"name": "STPC Archived Mapping", "company_id": self.company_a.id,
                              "pipeline_category_ids": [Command.link(self.category_a.id)]})

    def test_stpc03_category_and_native_team_stages_intersect(self):
        lead = self._lead(self.category_shared)
        self.assertEqual(lead.stage_id, self.stage_common)
        scoped = self.Lead.with_context(
            pipeline_category_scope_id=self.category_shared.id,
            default_team_id=self.team_other.id, show_team_switcher=True,
        )
        columns = scoped._read_group_stage_ids(self.Stage, [])
        self.assertIn(self.stage_common, columns)
        self.assertNotIn(self.stage_a, columns)
        with self.assertRaises(ValidationError):
            self._lead(self.category_shared, team_id=self.team_other.id, stage_id=self.stage_a.id)
        with self.assertRaises(ValidationError):
            lead.stage_id = self.stage_other

    def test_stpc03_won_bulk_lost_and_restore_remain_native(self):
        leads = self._lead(self.category_a) | self._lead(self.category_shared, team_id=self.team_other.id)
        leads.action_set_lost()
        self.assertFalse(any(leads.mapped("active")))
        leads.action_unarchive()
        leads.action_set_won()
        leads[0].action_set_won_rainbowman()
        self.assertEqual(leads.stage_id, self.won)
        self.assertEqual(leads.mapped("probability"), [100, 100])

    def test_stpc04_compatible_team_change_keeps_category_and_stage(self):
        lead = self._lead(self.category_shared)
        lead.team_id = self.team_other
        self.assertEqual(lead.pipeline_category_id, self.category_shared)
        self.assertEqual(lead.stage_id, self.stage_common)

    def test_stpc04_incompatible_team_change_is_rejected_without_clearing(self):
        lead = self._lead(self.category_a, expected_revenue=123)
        with self.assertRaises(ValidationError):
            lead.write({"team_id": self.team_other.id, "expected_revenue": 999})
        self.assertEqual(lead.team_id, self.team_a)
        self.assertEqual(lead.pipeline_category_id, self.category_a)
        self.assertEqual(lead.expected_revenue, 123)
        lead.write({"team_id": self.team_other.id, "pipeline_category_id": self.category_other.id})
        self.assertEqual(lead.pipeline_category_id, self.category_other)
        lead.write({"team_id": self.team_empty.id, "pipeline_category_id": False})
        self.assertFalse(lead.pipeline_category_id)

    def test_stpc04_native_stage_recomputation_is_not_suppressed(self):
        lead = self._lead(self.category_shared, stage_id=self.stage_a.id)
        lead.team_id = self.team_other
        self.assertEqual(lead.stage_id, self.stage_common)
        self.assertEqual(lead.pipeline_category_id, self.category_shared)

    def test_stpc04_warning_does_not_block_team_correction_or_clear_category(self):
        draft = self.Lead.new(self._values(self.category_a, team_id=self.team_other.id))
        result = draft._onchange_pipeline_team_category()
        self.assertEqual(result["warning"]["type"], "notification")
        self.assertEqual(draft.pipeline_category_id._origin, self.category_a)
        draft.team_id = self.team_a
        self.assertFalse(draft._onchange_pipeline_team_category())

    def test_stpc05_create_rpc_and_context_spoofing_rejected(self):
        for context in ({}, {"pipeline_category_scope_id": self.category_other.id,
                             "skip_pipeline_validation": True, "tracking_disable": True}):
            with self.assertRaises(ValidationError):
                self.Lead.with_context(**context).create(self._values(self.category_a, team_id=self.team_other.id))

    def test_stpc05_batch_create_and_write_are_atomic(self):
        before = self.Lead.search_count([("name", "=", "STPC Atomic")])
        with self.assertRaises(ValidationError):
            self.Lead.create([
                self._values(self.category_a, name="STPC Atomic"),
                self._values(self.category_a, name="STPC Atomic", team_id=self.team_other.id),
            ])
        self.assertEqual(self.Lead.search_count([("name", "=", "STPC Atomic")]), before)
        leads = self._lead(self.category_a) | self._lead(self.category_shared)
        with self.assertRaises(ValidationError):
            leads.write({"team_id": self.team_other.id})
        self.assertEqual(leads.team_id, self.team_a)

    def test_stpc05_real_import_uses_same_invariant(self):
        fields = ["name", "type", "user_id/.id", "team_id/.id", "company_id/.id", "pipeline_category_id/.id"]
        valid = ["STPC Imported", "opportunity", "", str(self.team_a.id), str(self.company_a.id), str(self.category_a.id)]
        result = self.Lead.load(fields, [valid])
        self.assertTrue(result["ids"], result["messages"])
        invalid = valid.copy()
        invalid[0], invalid[3] = "STPC Bad Import", str(self.team_other.id)
        result = self.Lead.load(fields, [invalid])
        self.assertFalse(result["ids"])
        self.assertTrue(any(message["type"] == "error" for message in result["messages"]))
        self.assertFalse(self.Lead.search([("name", "=", "STPC Bad Import")]))

    def test_stpc06_missing_team_and_empty_mapping_are_not_unrestricted(self):
        for team_id in (False, self.team_empty.id):
            with self.assertRaises(ValidationError):
                self._lead(self.category_a, team_id=team_id)
            self.assertFalse(self._lead(False, team_id=team_id).pipeline_category_id)

    def test_stpc06_no_automatic_category_or_mapping(self):
        self.assertFalse(self._lead(False).pipeline_category_id)
        self.assertFalse(self.team_empty.pipeline_category_ids)
        starter = self.Category.search([("s_name", "=", "General Sales"), ("company_id", "=", False)])
        self.assertTrue(starter)
        self.assertFalse(starter.sales_team_ids)

    def test_stpc06_companyless_team_requires_shared_categories(self):
        lead = self._lead(self.category_shared, team_id=self.team_global.id, company_id=False)
        self.assertFalse(lead.company_id)
        for team in (self.team_global, self.team_a):
            with self.assertRaises(ValidationError):
                team.write({"pipeline_category_ids": [Command.link(self.category_b.id)]})
        with self.assertRaises(ValidationError):
            self._lead(self.category_a, team_id=self.team_global.id, company_id=False)

    def test_stpc07_used_mapping_cannot_be_removed_for_any_history_state(self):
        for state in ("open", "archived", "won", "lost"):
            with self.subTest(state=state), self.cr.savepoint():
                lead = self._lead(self.category_a)
                if state == "archived":
                    lead.action_archive()
                elif state == "won":
                    lead.action_set_won()
                elif state == "lost":
                    lead.action_set_lost()
                for command in (Command.unlink(self.category_a.id), Command.clear(), Command.set(self.category_shared.ids)):
                    with self.assertRaisesRegex(ValidationError, "including archived, Won and Lost"):
                        self.team_a.write({"pipeline_category_ids": [command]})
                lead.pipeline_category_id = False
                self.team_a.write({"pipeline_category_ids": [Command.unlink(self.category_a.id)]})
                self.team_a.write({"pipeline_category_ids": [Command.link(self.category_a.id)]})

    def test_stpc07_hidden_usage_error_is_generic(self):
        lead = self._lead(self.category_shared, name="STPC SECRET HISTORY", team_id=self.team_b.id,
                          company_id=self.company_b.id)
        lead.action_set_lost()
        # The shared category's company scope also protects hidden team links.
        restricted = self.category_shared.with_user(self.manager).with_context(allowed_company_ids=self.company_a.ids)
        with self.assertRaises(ValidationError) as error:
            restricted.company_id = self.company_a
        self.assertNotIn(lead.name, str(error.exception))
        self.assertNotIn(self.team_b.name, str(error.exception))

    def test_stpc07_category_scope_checks_unused_and_archived_hidden_teams(self):
        self.team_b.active = False
        with self.assertRaisesRegex(ValidationError, "sales-team mappings"):
            self.category_shared.with_user(self.manager).with_context(
                allowed_company_ids=self.company_a.ids,
            ).write({"company_id": self.company_a.id})

    def test_stpc07_mapping_removal_checks_hidden_company_history(self):
        lead = self._lead(self.category_shared, name="STPC Hidden Company History",
                          team_id=self.team_global.id, company_id=self.company_b.id,
                          user_id=self.manager.id)
        lead.action_set_lost()
        manager_team = self.team_global.with_user(self.manager).with_context(allowed_company_ids=self.company_a.ids)
        self.assertFalse(self.Lead.with_env(manager_team.env).with_context(active_test=False).search([("id", "=", lead.id)]))
        with self.assertRaisesRegex(ValidationError, "existing categorized CRM records") as error:
            manager_team.write({"pipeline_category_ids": [Command.clear()]})
        self.assertNotIn(lead.name, str(error.exception))
        self.assertIn(self.category_shared, self.team_global.pipeline_category_ids)

    def test_stpc07_team_company_change_cannot_invalidate_history(self):
        self._lead(self.category_shared)
        self.team_a.write({"pipeline_category_ids": [Command.set(self.category_shared.ids)]})
        with self.assertRaisesRegex(ValidationError, "existing categorized CRM records"):
            self.team_a.company_id = self.company_b

    def test_stpc07_archive_preserves_history_but_rejects_new_assignments(self):
        lead = self._lead(self.category_a)
        self.team_a.active = False
        self.category_a.active = False
        self.assertIn(self.category_a, self.team_a.pipeline_category_ids)
        self.assertIn(self.team_a, self.category_a.sales_team_ids)
        lead.write({"name": "STPC History Note", "description": "Still editable"})
        lead.write({"pipeline_category_id": self.category_a.id, "team_id": self.team_a.id})
        with self.assertRaises(ValidationError):
            lead.copy({"name": "STPC Archived Copy"})
        with self.assertRaises(ValidationError):
            self._lead(self.category_shared)
        with self.assertRaises(ValidationError):
            self._lead(False, team_id=self.team_other.id).write({
                "team_id": self.team_a.id, "pipeline_category_id": self.category_shared.id,
            })

    def test_stpc07_team_deletion_protects_hidden_archived_history(self):
        self._lead(self.category_a).action_set_lost()
        with self.assertRaisesRegex(UserError, "historical records"):
            self.team_a.unlink()
        unused = self.Team.create({"name": "STPC Unused", "company_id": self.company_a.id})
        unused.unlink()
        self.assertFalse(unused.exists())

    def test_stpc08_native_sales_manager_permissions(self):
        with self.assertRaises(AccessError):
            self.team_a.with_user(self.sales).write({"pipeline_category_ids": [Command.clear()]})
        self.team_empty.with_user(self.manager).write({"pipeline_category_ids": [Command.link(self.category_shared.id)]})
        self.assertIn(self.category_shared, self.team_empty.pipeline_category_ids)

    def test_stpc08_mapping_does_not_grant_record_access(self):
        lead = self._lead(self.category_shared, user_id=self.manager.id)
        sales_env = self.Lead.with_user(self.sales).with_context(allowed_company_ids=self.company_a.ids).env
        self.assertTrue(self.category_shared.with_env(sales_env).read(["s_name"]))
        self.assertFalse(self.Lead.with_env(sales_env).search([("id", "=", lead.id)]))
        self.assertFalse(self.Team.with_env(sales_env).search([("id", "=", self.team_b.id)]))
        with self.assertRaises(AccessError):
            self.team_a.with_user(self.manager).with_context(allowed_company_ids=self.company_a.ids).write({
                "pipeline_category_ids": [Command.link(self.category_b.id)],
            })

    def test_stpc09_dirty_form_keeps_classification_and_does_not_autosave(self):
        lead = self._lead(self.category_a, expected_revenue=100)
        form = Form(lead, view="crm.crm_lead_view_form")
        form.expected_revenue = 4321
        with self.assertLogs("odoo.tests.form.onchange", level="WARNING") as notification:
            form.team_id = self.team_other
        self.assertEqual(len(notification.output), 1)
        self.assertRegex(notification.output[0], r"^WARNING:.*:Category not available to this team ")
        self.assertEqual(form.pipeline_category_id, self.category_a)
        self.assertEqual(lead.team_id, self.team_a)
        self.assertEqual(lead.expected_revenue, 100)
        with self.assertRaises(ValidationError):
            form.save()
        form.pipeline_category_id = self.category_other
        form.save()
        self.assertEqual(lead.expected_revenue, 4321)
        self.assertEqual(lead.pipeline_category_id, self.category_other)
        self.env.invalidate_all()
        self.assertEqual(lead.team_id, self.team_other)

    def test_stpc10_scoped_quick_create_exposes_team_and_keeps_category(self):
        action = self.category_a.action_open_pipeline()
        with self.assertLogs("odoo.tests.form.onchange", level="WARNING") as notification:
            form = Form(self.Lead.with_context(
                **action["context"], default_user_id=False, default_team_id=self.team_other.id,
            ), view="crm.quick_create_opportunity_form")
        self.assertEqual(len(notification.output), 1)
        self.assertRegex(notification.output[0], r"^WARNING:.*:Category not available to this team ")
        form.name = "STPC Quick Create"
        self.assertEqual(form.pipeline_category_id, self.category_a)
        form.team_id = self.team_a
        lead = form.save()
        self.assertEqual(lead.team_id, self.team_a)
        self.assertEqual(lead.pipeline_category_id, self.category_a)
        self.assertEqual(lead.stage_id, self.stage_common)

    def test_stpc10_conversion_and_duplication(self):
        lead = self._lead(self.category_a, type="lead")
        partner = self.env["res.partner"].create({"name": "STPC Customer"})
        lead.convert_opportunity(partner, user_ids=self.sales.ids, team_id=self.team_a.id)
        self.assertEqual(lead.type, "opportunity")
        self.assertEqual(lead.pipeline_category_id, self.category_a)
        self.assertEqual(lead.copy({"name": "STPC Copied"}).pipeline_category_id, self.category_a)

    def test_stpc10_merge_preserves_matching_classification(self):
        lead = self._lead(self.category_a)
        merged = (lead | self._lead(self.category_a))._merge_opportunity()
        self.assertEqual(merged.pipeline_category_id, self.category_a)
        with self.assertRaises(UserError):
            (merged | self._lead(self.category_shared))._merge_opportunity()

    def test_stpc10_assignment_rejects_incompatible_category_explicitly(self):
        lead = self._lead(self.category_a)
        with self.assertRaises(ValidationError):
            lead._handle_salesmen_assignment(team_id=self.team_other.id)
        self.assertEqual(lead.team_id, self.team_a)
        shared = self._lead(self.category_shared)
        shared._handle_salesmen_assignment(team_id=self.team_other.id)
        self.assertEqual(shared.team_id, self.team_other)

    def test_stpc10_salesperson_recompute_checks_final_team(self):
        lead = self._lead(self.category_a)
        with self.assertRaises(ValidationError):
            lead.user_id = self.other_sales
        self.assertEqual(lead.team_id, self.team_a)
        shared = self._lead(self.category_shared)
        shared.user_id = self.other_sales
        self.assertEqual(shared.team_id, self.team_other)

    def test_stpc11_legacy_report_is_read_only_and_incremental_mapping_is_possible(self):
        legacy_a = self._legacy(self.category_a, team_id=self.team_empty.id)
        legacy_shared = self._legacy(self.category_shared, team_id=self.team_empty.id)
        legacy_shared.action_set_lost()
        fields = ["name", "team_id", "pipeline_category_id", "stage_id", "active", "write_date"]
        records = legacy_a | legacy_shared
        before = records.read(fields)
        action = self.Lead.with_user(self.manager).action_open_pipeline_team_compatibility()
        self.assertEqual(self.Lead.with_context(active_test=False).search(action["domain"]) & records, records)
        self.assertEqual(records.read(fields), before)
        legacy_a.write({"description": "Allowed unrelated legacy edit"})
        with self.assertRaises(ValidationError):
            legacy_a.stage_id = self.stage_a
        self.team_empty.write({"pipeline_category_ids": [Command.link(self.category_a.id)]})
        action = self.Lead.with_user(self.manager).action_open_pipeline_team_compatibility()
        self.assertEqual(self.Lead.with_context(active_test=False).search(action["domain"]) & records, legacy_shared)
        self.team_empty.write({"pipeline_category_ids": [Command.link(self.category_shared.id)]})
        action = self.Lead.with_user(self.manager).action_open_pipeline_team_compatibility()
        self.assertFalse(self.Lead.with_context(active_test=False).search(action["domain"]) & records)

    def test_stpc11_report_permissions_and_company_visibility(self):
        with self.assertRaises(AccessError):
            self.Lead.with_user(self.sales).action_open_pipeline_team_compatibility()
        hidden = self._legacy(self.category_shared, team_id=False, company_id=self.company_b.id)
        action = self.Lead.with_user(self.manager).with_context(
            allowed_company_ids=self.company_a.ids,
        ).action_open_pipeline_team_compatibility()
        visible = self.Lead.with_user(self.manager).with_context(
            allowed_company_ids=self.company_a.ids, active_test=False,
        ).search(action["domain"])
        self.assertNotIn(hidden, visible)

    def test_stpc11_second_company_configuration_without_code_changes(self):
        lead = self._lead(self.category_b, team_id=self.team_b.id, company_id=self.company_b.id)
        lead.action_set_won()
        self.assertEqual(lead.stage_id, self.won)
        self.assertEqual(lead.company_id, self.company_b)

    def test_stpc12_no_optional_engine_dependency_and_views_are_native_extensions(self):
        module = self.env["ir.module.module"].search([("name", "=", "kpability_sales_team_pipeline_categories")])
        self.assertEqual(module.dependencies_id.mapped("name"), ["kpability_pipeline_categories"])
        quick = etree.fromstring(self.env["crm.lead"].get_view(
            self.env.ref("crm.quick_create_opportunity_form").id, "form",
        )["arch"])
        self.assertEqual(quick.xpath("//field[@name='team_id']")[0].get("invisible"), "False")
        self.assertTrue(quick.xpath("//field[@name='pipeline_team_category_ids']"))
        for xml_id in ("crm_lead_view_list_compatibility", "crm_lead_view_form_compatibility"):
            arch = etree.fromstring(self.env.ref(f"kpability_sales_team_pipeline_categories.{xml_id}").arch_db)
            self.assertEqual(arch.get("edit"), "0")
