from odoo import Command
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestWebsitePipelineCategoryAvailability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].search([], limit=1)
        cls.stage = cls.env["crm.stage"].create({"name": "Website PC Intake", "sequence": 11})
        cls.Category = cls.env["crm.pipeline.category"]
        cls.category = cls.Category.create({
            "s_name": "Website PC Enrollment",
            "company_id": False,
            "stage_ids": [Command.set(cls.stage.ids)],
            "website_ids": [Command.set(cls.website.ids)],
        })

    def test_available_categories_are_limited_to_configured_websites(self):
        self.assertIn(self.category, self.Category._get_website_categories(self.website))
        other = self.Category.create({
            "s_name": "Website PC Hidden",
            "company_id": False,
            "stage_ids": [Command.set(self.stage.ids)],
        })
        self.assertNotIn(other, self.Category._get_website_categories(self.website))
        self.assertFalse(other._is_available_on_website(self.website))
        self.assertTrue(self.category._is_available_on_website(self.website))
        self.category.active = False
        self.assertFalse(self.category._is_available_on_website(self.website))


@tagged("post_install", "-at_install")
class TestWebsitePipelineCategoryHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].search([], limit=1)
        cls.stage = cls.env["crm.stage"].create({"name": "Website PC HTTP Intake", "sequence": 12})
        cls.category_a = cls.env["crm.pipeline.category"].create({
            "s_name": "Website PC HTTP A",
            "company_id": False,
            "stage_ids": [Command.set(cls.stage.ids)],
            "website_ids": [Command.set(cls.website.ids)],
        })
        cls.category_b = cls.env["crm.pipeline.category"].create({
            "s_name": "Website PC HTTP B",
            "company_id": False,
            "stage_ids": [Command.set(cls.stage.ids)],
            "website_ids": [Command.set(cls.website.ids)],
        })

    def setUp(self):
        super().setUp()
        self.authenticate(None, None, session_extra={"force_website_id": self.website.id})

    def test_public_endpoint_lists_available_pipelines(self):
        response = self.url_open("/kpability/pipeline-categories")
        self.assertEqual(response.status_code, 200)
        payload = response.json()
        ids = {item["id"] for item in payload}
        self.assertIn(self.category_a.id, ids)
        self.assertIn(self.category_b.id, ids)

    def test_one_submission_creates_one_opportunity_per_pipeline(self):
        email = "website-pc@example.test"
        response = self.url_open("/website/form/crm.lead", data={
            "name": "Website PC Request",
            "email_from": email,
            "description": "Please contact me about enrollment.",
            f"kp_pipeline_category_id_{self.category_a.id}": self.category_a.id,
            f"kp_pipeline_category_id_{self.category_b.id}": self.category_b.id,
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json().get("id"))
        leads = self.env["crm.lead"].sudo().search([("email_from", "ilike", email)])
        self.assertEqual(leads.mapped("pipeline_category_id"), self.category_a | self.category_b)
