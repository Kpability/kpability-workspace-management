from ast import literal_eval

from psycopg2 import IntegrityError

from odoo import Command
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import Form, TransactionCase, new_test_user, tagged
from odoo.tools import mute_logger


@tagged("post_install", "-at_install")
class TestPipelineCategories(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a, cls.company_b = cls.env["res.company"].create([
            {"name": "PC Company A"},
            {"name": "PC Company B"},
        ])
        cls.env = cls.env(context={
            **cls.env.context,
            "allowed_company_ids": [cls.company_a.id, cls.company_b.id],
            "mail_create_nolog": True,
            "mail_notrack": True,
        })
        cls.Category = cls.env["crm.pipeline.category"]
        cls.Lead = cls.env["crm.lead"]
        cls.Stage = cls.env["crm.stage"]
        cls.team_a, cls.team_b = cls.env["crm.team"].create([
            {"name": "PC Team A", "company_id": cls.company_a.id},
            {"name": "PC Team B", "company_id": cls.company_b.id},
        ])
        cls.manager = new_test_user(
            cls.env, login="pc_manager", groups="sales_team.group_sale_manager,base.group_multi_company",
            company_id=cls.company_a.id,
            company_ids=[Command.set((cls.company_a | cls.company_b).ids)],
        )
        cls.sales = new_test_user(
            cls.env, login="pc_sales", groups="sales_team.group_sale_salesman,base.group_multi_company",
            company_id=cls.company_a.id,
            company_ids=[Command.set((cls.company_a | cls.company_b).ids)],
        )
        cls.sales_a = new_test_user(
            cls.env, login="pc_sales_a", groups="sales_team.group_sale_salesman",
            company_id=cls.company_a.id,
        )
        cls.internal = new_test_user(
            cls.env, login="pc_internal", groups="base.group_user", company_id=cls.company_a.id,
        )
        (
            cls.stage_common, cls.stage_a, cls.stage_renewal, cls.stage_b,
            cls.won_a, cls.won_renewal, cls.won_b,
        ) = cls.Stage.create([
            {"name": "PC Shared Intake", "sequence": 10},
            {"name": "PC A Qualification", "sequence": 20, "team_ids": [Command.set(cls.team_a.ids)]},
            {"name": "PC Renewal Review", "sequence": 30},
            {"name": "PC B Qualification", "sequence": 40, "team_ids": [Command.set(cls.team_b.ids)]},
            {"name": "PC A Won", "sequence": 90, "is_won": True, "team_ids": [Command.set(cls.team_a.ids)]},
            {"name": "PC Renewal Won", "sequence": 95, "is_won": True},
            {"name": "PC B Won", "sequence": 100, "is_won": True, "team_ids": [Command.set(cls.team_b.ids)]},
        ])
        cls.category_a, cls.category_shared, cls.category_b = cls.Category.create([
            {
                "s_name": "PC New Business", "company_id": cls.company_a.id, "n_sequence": 10,
                "stage_ids": [Command.set((cls.stage_common | cls.stage_a | cls.won_a).ids)],
            },
            {
                "s_name": "PC Renewals", "company_id": False, "n_sequence": 20,
                "stage_ids": [Command.set((cls.stage_common | cls.stage_renewal | cls.won_renewal).ids)],
            },
            {
                "s_name": "PC Company B", "company_id": cls.company_b.id, "n_sequence": 30,
                "stage_ids": [Command.set((cls.stage_common | cls.stage_b | cls.won_b).ids)],
            },
        ])

    def _lead_vals(self, category=None, **overrides):
        vals = {
            "name": "PC Opportunity", "type": "opportunity", "company_id": self.company_a.id,
            "team_id": self.team_a.id, "user_id": self.sales.id,
            "pipeline_category_id": category.id if category else False,
        }
        vals.update(overrides)
        return vals

    def _lead(self, category=None, **overrides):
        return self.Lead.create(self._lead_vals(category, **overrides))

    def test_pc01_category_crud_order_and_inverse_mapping(self):
        categories = (self.category_b | self.category_shared | self.category_a).sorted()
        self.assertEqual(categories, self.category_a | self.category_shared | self.category_b)
        self.assertEqual(self.category_a.display_name, self.category_a.s_name)
        self.assertIn(self.category_a, self.stage_common.pipeline_category_ids)
        self.assertIn(self.category_shared, self.stage_common.pipeline_category_ids)
        self.category_a.with_user(self.manager).write({"s_description": "Reusable category"})
        self.assertEqual(self.category_a.s_description, "Reusable category")
        empty = self.Category.with_user(self.manager).create({"s_name": "PC Empty", "company_id": False})
        empty.unlink()
        self.assertFalse(empty.exists())

    def test_pc02_normalized_company_name_uniqueness(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Category.create({"s_name": "  ＰＣ   NEW BUSINESS  ", "company_id": self.company_a.id})
            self.Category.flush_model()

    def test_pc02_normalized_shared_name_uniqueness(self):
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Category.create({"s_name": " pc   RENEWALS ", "company_id": False})
            self.Category.flush_model()

    def test_pc02_same_label_in_other_scopes(self):
        categories = self.Category.create([
            {"s_name": self.category_a.s_name, "company_id": self.company_b.id},
            {"s_name": self.category_a.s_name, "company_id": False},
        ])
        self.assertEqual(len(categories), 2)

    def test_pc02_blank_names_rejected(self):
        with self.assertRaises(ValidationError):
            self.Category.create({"s_name": "   ", "company_id": False})

    def test_pc03_initial_stage_is_category_and_team_eligible(self):
        lead = self._lead(self.category_a)
        self.assertEqual(lead.stage_id, self.stage_common)
        self.assertEqual(lead._stage_find(domain=[("is_won", "=", True)]), self.won_a)

    def test_pc03_empty_or_incompatible_mappings_do_not_mean_all(self):
        for stages in (self.Stage, self.stage_b):
            category = self.Category.create({
                "s_name": f"PC Unavailable {stages.ids}", "company_id": False,
                "stage_ids": [Command.set(stages.ids)],
            })
            with self.assertRaises(ValidationError):
                self._lead(category)
        with self.assertRaises(UserError):
            self.Category.create({"s_name": "PC No Stages", "company_id": False}).action_open_pipeline()

    def test_pc03_scoped_stage_columns_and_native_overview(self):
        scoped = self.Lead.with_context(
            pipeline_category_scope_id=self.category_a.id,
            show_team_switcher=True, default_team_id=self.team_a.id,
        )
        columns = scoped._read_group_stage_ids(self.Stage, [])
        self.assertEqual(columns, self.stage_common | self.stage_a | self.won_a)
        overview = self.Lead.with_context(
            show_team_switcher=True, default_team_id=self.team_a.id,
        )._read_group_stage_ids(self.Stage, [])
        self.assertIn(self.stage_renewal, overview)
        self.assertIn(self.stage_a, overview)
        self.assertNotIn(self.stage_b, overview)

    def test_pc04_explicit_incompatible_stage_on_create_rejected(self):
        with self.assertRaises(ValidationError):
            self._lead(self.category_a, stage_id=self.stage_renewal.id)

    def test_pc04_invalid_write_and_spoofed_context_rejected(self):
        lead = self._lead(self.category_a)
        with self.assertRaises(ValidationError):
            lead.with_context(pipeline_category_scope_id=self.category_shared.id).write({
                "stage_id": self.stage_renewal.id,
            })
        self.assertEqual(lead.stage_id, self.stage_common)

    def test_pc04_category_change_needs_explicit_compatible_stage(self):
        lead = self._lead(self.category_a, stage_id=self.stage_a.id)
        with self.assertRaises(ValidationError):
            lead.write({"pipeline_category_id": self.category_shared.id})
        self.assertEqual(lead.stage_id, self.stage_a)
        self.assertEqual(lead.pipeline_category_id, self.category_a)
        lead.write({"pipeline_category_id": self.category_shared.id, "stage_id": self.stage_renewal.id})
        self.assertEqual(lead.stage_id, self.stage_renewal)

    def test_pc04_native_team_restrictions_still_apply(self):
        category = self.Category.create({
            "s_name": "PC Wrong Team", "company_id": False,
            "stage_ids": [Command.set(self.stage_b.ids)],
        })
        with self.assertRaises(ValidationError):
            self._lead(category, stage_id=self.stage_b.id)

    def test_pc05_search_group_and_scoped_action_defaults(self):
        lead = self._lead(self.category_a)
        other = self._lead(self.category_shared)
        action = self.category_a.action_open_pipeline()
        native = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        self.assertEqual(action["views"], native["views"])
        self.assertEqual(action["view_mode"], native["view_mode"])
        self.assertEqual(action["context"]["default_pipeline_category_id"], self.category_a.id)
        self.assertEqual(action["context"]["default_company_id"], self.company_a.id)
        self.assertTrue(action["context"]["show_team_switcher"])
        self.assertNotIn("id", action)
        self.assertNotIn("path", action)
        self.assertIn(lead, self.Lead.search(action["domain"]))
        self.assertNotIn(other, self.Lead.search(action["domain"]))
        self.assertNotIn("pipeline_category_scope_id", literal_eval(native["context"]))
        grouped = self.Lead._read_group(
            [("id", "in", (lead | other).ids)], ["pipeline_category_id"], ["__count"],
        )
        self.assertEqual({category.id: count for category, count in grouped}, {
            self.category_a.id: 1, self.category_shared.id: 1,
        })

    def test_pc06_archive_preserves_history_and_blocks_new_assignments(self):
        lead = self._lead(self.category_a)
        self.category_a.active = False
        self.assertEqual(lead.pipeline_category_id.display_name, self.category_a.s_name)
        lead.write({"name": "PC Historical Update"})
        lead.write({"pipeline_category_id": self.category_a.id})
        with self.assertRaises(ValidationError):
            self._lead(self.category_a)
        unclassified = self._lead(stage_id=self.stage_common.id)
        with self.assertRaises(ValidationError):
            unclassified.pipeline_category_id = self.category_a
        with self.assertRaises(IntegrityError), mute_logger("odoo.sql_db"):
            self.Category.create({"s_name": self.category_a.s_name, "company_id": self.company_a.id})
            self.Category.flush_model()

    def test_pc06_used_category_cannot_be_deleted(self):
        lead = self._lead(self.category_a)
        lead.action_archive()
        with self.assertRaises(UserError):
            self.category_a.unlink()

    def test_pc07_company_visibility_and_assignment(self):
        categories = self.Category.with_user(self.sales_a).with_context(allowed_company_ids=self.company_a.ids)
        visible = categories.search([])
        self.assertIn(self.category_a, visible)
        self.assertIn(self.category_shared, visible)
        self.assertNotIn(self.category_b, visible)
        with self.assertRaises(AccessError):
            categories.browse(self.category_b.id).read(["s_name"])
        with self.assertRaises((AccessError, ValidationError, UserError)):
            self.Lead.with_user(self.sales_a).with_context(allowed_company_ids=self.company_a.ids).create(
                self._lead_vals(self.category_b),
            )

    def test_pc07_cross_company_assignment_and_changes_rejected(self):
        with self.assertRaises((UserError, ValidationError)):
            self._lead(self.category_b)
        lead = self._lead(self.category_a)
        with self.assertRaises((UserError, ValidationError)):
            lead.write({"company_id": self.company_b.id, "team_id": self.team_b.id})
        shared = self._lead(
            self.category_shared, company_id=self.company_b.id, team_id=self.team_b.id,
        )
        self.assertEqual(shared.pipeline_category_id, self.category_shared)

    def test_pc07_companyless_records_only_accept_shared_categories(self):
        companyless = {"company_id": False, "team_id": False, "user_id": False}
        lead = self._lead(self.category_shared, **companyless)
        self.assertFalse(lead.company_id)
        with self.assertRaises((UserError, ValidationError)):
            self._lead(self.category_a, **companyless)

    def test_pc07_sales_read_only_and_non_crm_denied(self):
        category = self.category_shared.with_user(self.sales)
        self.assertTrue(category.read(["s_name"]))
        for operation in (
            lambda: category.write({"s_description": "Not allowed"}),
            lambda: self.Category.with_user(self.sales).create({"s_name": "Not allowed"}),
            lambda: category.unlink(),
        ):
            with self.assertRaises(AccessError):
                operation()
        with self.assertRaises(AccessError):
            self.category_shared.with_user(self.internal).read(["s_name"])

    def test_pc07_category_does_not_grant_lead_visibility(self):
        lead = self._lead(self.category_shared, user_id=self.manager.id)
        visible = self.Lead.with_user(self.sales).search([("id", "=", lead.id)])
        self.assertFalse(visible)
        self.assertTrue(self.category_shared.with_user(self.sales).read(["s_name"]))

    def test_pc08_draft_category_change_preserves_stage_and_other_values(self):
        lead = self._lead(self.category_a, stage_id=self.stage_a.id, expected_revenue=100)
        form = Form(lead, view="crm.crm_lead_view_form")
        form.expected_revenue = 4321
        form.pipeline_category_id = self.category_shared
        self.assertEqual(form.stage_id, self.stage_a)
        self.assertEqual(form.expected_revenue, 4321)
        self.assertEqual(lead.expected_revenue, 100)
        self.assertEqual(lead.pipeline_category_id, self.category_a)
        with self.assertRaises(ValidationError):
            form.save()
        form.stage_id = self.stage_renewal
        form.save()
        self.assertEqual(lead.expected_revenue, 4321)
        self.assertEqual(lead.pipeline_category_id, self.category_shared)

    def test_pc09_unclassified_native_behavior_is_unchanged(self):
        lead = self._lead(stage_id=self.stage_renewal.id)
        self.assertFalse(lead.pipeline_category_id)
        lead.stage_id = self.stage_a
        self.assertEqual(lead.stage_id, self.stage_a)
        lead.action_set_won()
        self.assertTrue(lead.stage_id.is_won)

    def test_pc09_scoped_quick_create_defaults(self):
        action = self.category_a.action_open_pipeline()
        model = self.Lead.with_context(
            **action["context"], default_team_id=self.team_a.id, default_user_id=self.sales.id,
        )
        with Form(model, view="crm.quick_create_opportunity_form") as form:
            form.name = "PC Scoped Quick Create"
            self.assertEqual(form.pipeline_category_id, self.category_a)
        self.assertEqual(form.record.pipeline_category_id, self.category_a)
        self.assertIn(form.record.stage_id, self.category_a.stage_ids)

    def test_pc10_mapping_removal_checks_hidden_and_archived_records(self):
        lead = self._lead(
            self.category_shared, stage_id=self.stage_renewal.id,
            company_id=self.company_b.id, team_id=self.team_b.id,
        )
        lead.action_archive()
        manager_a = self.category_shared.with_user(self.manager).with_context(
            allowed_company_ids=self.company_a.ids,
        )
        with self.assertRaisesRegex(ValidationError, "existing leads or opportunities"):
            manager_a.write({"stage_ids": [Command.unlink(self.stage_renewal.id)]})
        self.assertIn(self.stage_renewal, self.category_shared.stage_ids)
        lead.pipeline_category_id = False
        manager_a.write({"stage_ids": [Command.unlink(self.stage_renewal.id)]})
        self.assertNotIn(self.stage_renewal, self.category_shared.stage_ids)

    def test_pc10_company_scope_change_cannot_invalidate_records(self):
        self._lead(
            self.category_shared, company_id=self.company_b.id, team_id=self.team_b.id,
        )
        with self.assertRaises(ValidationError):
            self.category_shared.company_id = self.company_a

    def test_pc10_stage_inverse_cannot_erase_hidden_mappings(self):
        with self.assertRaises(UserError):
            self.stage_common.with_user(self.manager).write({"pipeline_category_ids": [Command.clear()]})
        copied = self.stage_common.copy({"name": "PC Stage Copy"})
        self.assertFalse(copied.pipeline_category_ids)

    def test_pc10_stage_team_edit_checks_existing_categorized_records(self):
        lead = self._lead(self.category_shared)
        lead.action_archive()
        with self.assertRaises(ValidationError):
            self.stage_common.write({"team_ids": [Command.set(self.team_b.ids)]})

    def test_pc11_independent_category_dataset(self):
        stage = self.Stage.create({"name": "PC Second Client Intake", "sequence": 5})
        category = self.Category.create({
            "s_name": "PC Second Client", "company_id": False, "stage_ids": [Command.set(stage.ids)],
        })
        lead = self._lead(category)
        self.assertEqual(lead.stage_id, stage)
        self.assertNotIn(stage, self.category_a.stage_ids)

    def test_won_bulk_uses_each_category_and_team(self):
        lead_a = self._lead(self.category_a, stage_id=self.stage_a.id)
        renewal = self._lead(self.category_shared, stage_id=self.stage_renewal.id)
        lead_b = self._lead(self.category_b, company_id=self.company_b.id, team_id=self.team_b.id)
        (lead_a | renewal | lead_b).action_set_won()
        self.assertEqual(lead_a.stage_id, self.won_a)
        self.assertEqual(renewal.stage_id, self.won_renewal)
        self.assertEqual(lead_b.stage_id, self.won_b)
        self.assertEqual((lead_a | renewal | lead_b).mapped("probability"), [100, 100, 100])

    def test_missing_won_stage_rejects_bulk_before_writes(self):
        no_won = self.Category.create({
            "s_name": "PC No Won", "company_id": False,
            "stage_ids": [Command.set(self.stage_common.ids)],
        })
        valid = self._lead(self.category_a)
        invalid = self._lead(no_won)
        unclassified = self._lead()
        unclassified.action_set_lost()
        with self.assertRaisesRegex(UserError, "No Won stage"):
            (unclassified | valid | invalid).action_set_won()
        self.assertEqual(valid.stage_id, self.stage_common)
        self.assertFalse(unclassified.active)
        self.assertEqual(unclassified.probability, 0)

    def test_native_lost_restore_and_rainbowman(self):
        lead = self._lead(self.category_a)
        lead.action_set_lost()
        self.assertFalse(lead.active)
        self.assertEqual(lead.probability, 0)
        self.assertEqual(lead.pipeline_category_id, self.category_a)
        lead.action_unarchive()
        lead.action_set_won_rainbowman()
        self.assertTrue(lead.active)
        self.assertEqual(lead.stage_id, self.won_a)
        self.assertEqual(lead.probability, 100)

    def test_conversion_and_duplication_preserve_classification(self):
        lead = self._lead(self.category_a, type="lead", stage_id=self.stage_a.id)
        partner = self.env["res.partner"].create({"name": "PC Customer"})
        lead.convert_opportunity(partner, user_ids=self.sales.ids, team_id=self.team_a.id)
        self.assertEqual(lead.type, "opportunity")
        self.assertEqual(lead.pipeline_category_id, self.category_a)
        copied = lead.copy({"name": "PC Copied Opportunity"})
        self.assertEqual(copied.pipeline_category_id, self.category_a)
        self.assertIn(copied.stage_id, self.category_a.stage_ids)

    def test_merge_conflicting_classifications_rejected(self):
        lead = self._lead(self.category_a)
        for other in (self._lead(self.category_shared), self._lead()):
            with self.assertRaises(UserError):
                (lead | other)._merge_opportunity()
            self.assertTrue(other.exists())

    def test_merge_matching_classification_preserved(self):
        leads = self._lead(self.category_a) | self._lead(self.category_a)
        merged = leads._merge_opportunity()
        self.assertEqual(merged.pipeline_category_id, self.category_a)
        self.assertIn(merged.stage_id, self.category_a.stage_ids)

    def test_batch_creation_and_bulk_stage_write(self):
        leads = self.Lead.create([
            self._lead_vals(self.category_a, name=f"PC Batch {index}") for index in range(50)
        ])
        self.assertEqual(len(leads), 50)
        self.assertEqual(leads.stage_id, self.stage_common)
        leads.write({"stage_id": self.stage_a.id})
        self.assertEqual(leads.stage_id, self.stage_a)
        with self.assertRaises(ValidationError):
            leads.write({"stage_id": self.stage_renewal.id})
        self.assertEqual(leads.stage_id, self.stage_a)

    def test_scope_does_not_bypass_category_access(self):
        with self.assertRaises(AccessError):
            self.Lead.with_user(self.sales_a).with_context(
                allowed_company_ids=self.company_a.ids,
                pipeline_category_scope_id=self.category_b.id,
            )._read_group_stage_ids(self.Stage, [])
        with self.assertRaises(UserError):
            self.Lead.with_context(pipeline_category_scope_id=-1)._read_group_stage_ids(self.Stage, [])
