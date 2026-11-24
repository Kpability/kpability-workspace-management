from odoo import Command
from odoo.tests import HttpCase, TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestRetiredWebsitePipelineConfiguration(TransactionCase):
    def test_website_mapping_is_storage_only(self):
        website = self.env["website"].search([], limit=1)
        category = self.env["crm.pipeline.category"].create({
            "s_name": "Retired Website Mapping", "company_id": False,
            "website_ids": [Command.set(website.ids)],
        })
        self.assertEqual(category.website_ids, website)
        self.assertTrue(category._fields["website_ids"].readonly)
        self.assertFalse(hasattr(category, "_get_website_categories"))
        self.assertFalse(hasattr(category, "_is_available_on_website"))

    def test_website_configuration_and_snippet_are_inactive(self):
        for xml_id in ("crm_pipeline_category_view_form_website", "snippets"):
            self.assertFalse(self.env.ref(f"kpability_website_pipeline_categories.{xml_id}").active)

    def test_legacy_template_is_non_interactive(self):
        template = self.env.ref("kpability_website_pipeline_categories.pipeline_category_form")
        self.assertNotIn("<form", template.arch_db)
        self.assertNotIn("data-kp-pipeline-categories", template.arch_db)
        self.assertIn("intake is unavailable", template.arch_db)


@tagged("post_install", "-at_install")
class TestRetiredWebsitePipelineHttp(HttpCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.website = cls.env["website"].search([], limit=1)

    def setUp(self):
        super().setUp()
        self.authenticate(None, None, session_extra={"force_website_id": self.website.id})

    def test_public_category_endpoint_is_removed(self):
        self.assertEqual(self.url_open("/kpability/pipeline-categories").status_code, 404)

    def test_cached_checkbox_submission_is_rejected(self):
        name = "Retired Website Checkbox Submission"
        response = self.url_open("/website/form/crm.lead", data={
            "name": name, "email_from": "pc-retired-checkbox@example.test",
            "kp_pipeline_category_id_1": "1",
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn("intake is unavailable", response.json()["error"])
        self.assertFalse(self.env["crm.lead"].sudo().search([("name", "=", name)]))

    def test_cached_list_submission_and_attachment_are_rejected(self):
        name = "Retired Website List Submission"
        response = self.url_open("/website/form/crm.lead", data={
            "name": name, "email_from": "pc-retired-list@example.test",
            "kp_pipeline_category_ids": "1,2",
        }, files={"attachment": ("retired.txt", b"Must not be stored", "text/plain")})
        self.assertIn("intake is unavailable", response.json()["error"])
        self.assertFalse(self.env["crm.lead"].sudo().search([("name", "=", name)]))
        self.assertFalse(self.env["ir.attachment"].sudo().search([("name", "=", "retired.txt")]))

    def test_native_crm_website_form_still_creates_one_unclassified_record(self):
        name = "Native Website CRM Still Works"
        response = self.url_open("/website/form/crm.lead", data={
            "name": name, "email_from": "pc-native-form@example.test",
        })
        self.assertTrue(response.json().get("id"), response.text)
        leads = self.env["crm.lead"].sudo().search([("name", "=", name)])
        self.assertEqual(len(leads), 1)
        self.assertFalse(leads.pipeline_category_id)

    def test_existing_template_reference_remains_renderable_without_a_form(self):
        page = self.env["website.page"].create({
            "name": "Retired Pipeline Template", "type": "qweb",
            "key": "kpability_website_pipeline_categories.retired_http_test",
            "url": "/pc-retired-template", "website_id": self.website.id,
            "is_published": True,
            "arch": '<t t-call="website.layout"><div id="wrap">'
                    '<t t-call="kpability_website_pipeline_categories.pipeline_category_form"/>'
                    '</div></t>',
        })
        response = self.url_open(page.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("intake is unavailable", response.text)
        self.assertNotIn('data-model_name="crm.lead"', response.text)
