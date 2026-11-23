"""Opt-in Playwright proof on a disposable localhost Odoo 20 Enterprise DB.

Not imported by the Odoo test loader. Retains synthetic fixtures and evidence.
Credentials come exclusively from the environment and are never saved.
"""

import json
import os
import re
import secrets
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright


class SalesTeamPipelineBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("ODOO_E2E_URL", "http://127.0.0.1:18030")
        cls.database = os.environ.get("ODOO_E2E_DATABASE", "kpability_pipeline_stpc_fresh_final")
        if (os.environ.get("ODOO_E2E_ALLOW_WRITES") != "1"
                or urlparse(cls.url).hostname not in {"127.0.0.1", "localhost", "::1"}
                or not cls.database.startswith("kpability_pipeline_stpc_")):
            raise unittest.SkipTest("Explicit opt-in and a disposable localhost kpability_pipeline_stpc_* DB are required")
        cls.debug_assets = os.environ.get("ODOO_E2E_DEBUG_ASSETS") == "1"
        cls.run_id = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        cls.output = Path(os.environ.get("ODOO_E2E_ARTIFACTS", "/tmp/opencode/kpability-stpc-browser")) / cls.run_id
        cls.output.mkdir(parents=True, exist_ok=False)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.context = cls.browser.new_context(
            base_url=cls.url, viewport={"width": 1440, "height": 1000},
            record_video_dir=str(cls.output / "video"), record_video_size={"width": 1440, "height": 1000},
        )
        session = cls.authenticate(cls.context, os.environ.get("ODOO_E2E_LOGIN", "admin"), os.environ["ODOO_E2E_PASSWORD"])
        assert session["server_version"].startswith("20.0+e"), "Odoo 20 Enterprise is required"
        cls.uid, cls.user_context = session["uid"], session["user_context"]
        cls.company = session["user_companies"]["current_company"]
        required = {"web_enterprise", "crm_enterprise", "kpability_pipeline_categories",
                    "kpability_sales_team_pipeline_categories"}
        module_records = cls.call("ir.module.module", "search_read", [[
            ["name", "in", sorted(required | {"crm_stage_reasons", "kpability_website_pipeline_categories"})],
            ["state", "=", "installed"],
        ]], fields=["name", "latest_version"])
        modules = {module["name"]: module["latest_version"] for module in module_records}
        assert required <= modules.keys(), f"Missing required modules: {sorted(required - modules.keys())}"
        cls.stage, cls.won = cls.call("crm.stage", "create", [[
            {"name": f"STPC E2E Intake {cls.run_id}", "sequence": -9000},
            {"name": f"STPC E2E Won {cls.run_id}", "sequence": 9000, "is_won": True},
        ]])
        cls.category_names = [f"STPC E2E {name} {cls.run_id}" for name in ("New Business", "Renewals", "Shared")]
        cls.category, cls.alternative, cls.shared = cls.call("crm.pipeline.category", "create", [[
            {"s_name": name, "company_id": cls.company if index < 2 else False,
             "stage_ids": [[6, 0, [cls.stage, cls.won]]]} for index, name in enumerate(cls.category_names)
        ]])
        cls.team_names = [f"STPC E2E {name} {cls.run_id}" for name in ("Alpha", "Alternative")]
        cls.team, cls.other_team = cls.call("crm.team", "create", [[
            {"name": name, "company_id": cls.company, "member_ids": [[4, cls.uid]],
             "pipeline_category_ids": [[6, 0, [category, cls.shared]]]}
            for name, category in zip(cls.team_names, (cls.category, cls.alternative))
        ]])
        cls.lead = cls.call("crm.lead", "create", [[cls.values("Existing Opportunity", cls.category)]])[0]
        cls.artifact_info = {
            "server_version": session["server_version"], "browser": cls.browser.version, "database": cls.database,
            "debug_assets": cls.debug_assets,
            "modules": modules,
            "run_id": cls.run_id, "teams": [cls.team, cls.other_team], "categories": [cls.category, cls.alternative, cls.shared],
            "lead": cls.lead, "cases": [],
        }
        (cls.output / "dataset.json").write_text(json.dumps(cls.artifact_info, indent=2) + "\n")

    @classmethod
    def authenticate(cls, client, login, password):
        payload = client.request.post("/web/session/authenticate", data={
            "jsonrpc": "2.0", "method": "call", "params": {"db": cls.database, "login": login, "password": password},
        }).json()
        if payload.get("error"):
            raise RuntimeError(payload["error"]["data"]["message"])
        return payload["result"]

    @classmethod
    def request(cls, model, method, args, *, client=None, **kwargs):
        kwargs.setdefault("context", cls.user_context)
        return (client or cls.context).request.post("/web/dataset/call_kw", data={
            "jsonrpc": "2.0", "method": "call",
            "params": {"model": model, "method": method, "args": args, "kwargs": kwargs},
        }).json()

    @classmethod
    def call(cls, model, method, args, **kwargs):
        payload = cls.request(model, method, args, **kwargs)
        if payload.get("error"):
            raise RuntimeError(payload["error"]["data"]["message"])
        return payload["result"]

    @classmethod
    def values(cls, name, category):
        return {"name": f"STPC E2E {name} {cls.run_id}", "type": "opportunity", "team_id": cls.team,
                "user_id": cls.uid, "company_id": cls.company, "pipeline_category_id": category,
                "stage_id": cls.stage, "expected_revenue": 100}

    def setUp(self):
        self.page = self.context.new_page()
        self.page.set_default_timeout(20000)
        self.errors = []
        self.page.on("pageerror", lambda error: self.errors.append(str(error)))

    def tearDown(self):
        self.page.screenshot(path=str(self.output / f"{self._testMethodName}.png"), full_page=True)
        video = self.page.video
        self.page.close()
        if video:
            video.save_as(str(self.output / "video" / f"{self._testMethodName}.webm"))
        self.artifact_info["cases"].append(self._testMethodName)
        (self.output / "dataset.json").write_text(json.dumps(self.artifact_info, indent=2) + "\n")
        self.assertEqual(self.errors, [], "Unexpected browser JavaScript error")

    @classmethod
    def tearDownClass(cls):
        cls.context.close()
        cls.browser.close()
        cls.playwright.stop()
        print(f"Browser evidence: {cls.output}")

    def open_backend(self, page, path):
        query = "?debug=assets" if self.debug_assets else ""
        page.goto(f"/odoo/{path}{query}", wait_until="domcontentloaded")

    def open_record(self, model, record_id):
        self.open_backend(self.page, f"{model}/{record_id}")
        self.page.locator(".o_form_view").wait_for()

    def choose_team(self, name):
        self.page.get_by_role("tab", name="Extra Info", exact=True).click()
        self.page.locator("[name='team_id'] input").first.fill(name)
        self.page.get_by_role("option", name=name, exact=True).click()

    def persisted(self, lead):
        return self.call("crm.lead", "read", [[lead], ["team_id", "pipeline_category_id", "expected_revenue"]])[0]

    def test_01_native_team_configuration_and_read_only_inverse(self):
        self.open_record("crm.team", self.team)
        self.page.get_by_role("tab", name="Pipeline Categories", exact=True).click()
        mapping = self.page.locator("[name='pipeline_category_ids']")
        expect(mapping).to_contain_text(self.category_names[0])
        expect(mapping).to_contain_text(self.category_names[2])
        expect(mapping.locator("input")).to_be_visible()
        self.page.screenshot(path=str(self.output / "STPC01-team-mapping.png"), full_page=True)
        self.open_record("crm.pipeline.category", self.category)
        inverse = self.page.locator("[name='sales_team_ids']")
        expect(inverse).to_contain_text(self.team_names[0])
        expect(inverse.locator("input")).to_have_count(0)

    def test_02_category_dropdown_intersects_team_mapping(self):
        self.open_record("crm.lead", self.lead)
        category = self.page.locator("[name='pipeline_category_id'] input").first
        category.fill("STPC E2E")
        expect(self.page.get_by_role("option", name=self.category_names[0], exact=True)).to_be_visible()
        expect(self.page.get_by_role("option", name=self.category_names[2], exact=True)).to_be_visible()
        expect(self.page.get_by_role("option", name=self.category_names[1], exact=True)).to_have_count(0)
        self.page.screenshot(path=str(self.output / "STPC02-team-category-options.png"), full_page=True)
        self.page.keyboard.press("Escape")
        self.assertEqual(self.persisted(self.lead)["pipeline_category_id"][0], self.category)

    def test_03_dirty_form_discard_and_explicit_reclassification(self):
        lead = self.call("crm.lead", "create", [[self.values("Dirty Form", self.category)]])[0]
        self.open_record("crm.lead", lead)
        revenue = self.page.locator("[name='expected_revenue'] input").first
        revenue.fill("4321")
        self.choose_team(self.team_names[1])
        category = self.page.locator("[name='pipeline_category_id'] input").first
        expect(category).to_have_value(self.category_names[0])
        self.assertEqual(self.persisted(lead)["expected_revenue"], 100)
        self.page.get_by_role("button", name="Discard all changes", exact=True).click()
        expect(category).to_have_value(self.category_names[0])
        expect(self.page.locator(".o_form_status_indicator_buttons")).to_have_class(re.compile("invisible"))
        self.assertEqual(self.persisted(lead)["expected_revenue"], 100)
        self.assertEqual(self.persisted(lead)["team_id"][0], self.team)
        self.page.screenshot(path=str(self.output / "STPC09-after-discard.png"), full_page=True)
        revenue.fill("4321")
        self.choose_team(self.team_names[1])
        category.fill(self.category_names[1])
        self.page.get_by_role("option", name=self.category_names[1], exact=True).click()
        self.page.get_by_role("button", name="Save manually", exact=True).click()
        expect(self.page.locator(".o_form_status_indicator_buttons")).to_have_class(re.compile("invisible"))
        self.page.reload(wait_until="domcontentloaded")
        expect(category).to_have_value(self.category_names[1])
        persisted = self.persisted(lead)
        self.assertEqual(persisted["team_id"][0], self.other_team)
        self.assertEqual(persisted["pipeline_category_id"][0], self.alternative)
        self.assertEqual(persisted["expected_revenue"], 4321)

    def test_04_invalid_save_and_rpc_are_atomic(self):
        self.open_record("crm.lead", self.lead)
        self.choose_team(self.team_names[1])
        self.page.get_by_role("button", name="Save manually", exact=True).click()
        expect(self.page.get_by_role("dialog")).to_contain_text("Choose a sales team mapped")
        result = self.request("crm.lead", "write", [[self.lead], {"team_id": self.other_team}])
        self.assertEqual(result["error"]["data"]["name"], "odoo.exceptions.ValidationError")
        persisted = self.persisted(self.lead)
        self.assertEqual(persisted["team_id"][0], self.team)
        self.assertEqual(persisted["pipeline_category_id"][0], self.category)

    def test_05_category_scoped_quick_create_exposes_team(self):
        self.open_record("crm.pipeline.category", self.category)
        self.page.get_by_role("button", name="Open Pipeline", exact=True).click()
        expect(self.page.locator(".o_kanban_renderer")).to_be_visible()
        self.page.locator(".o_kanban_header .o_kanban_quick_add").first.click()
        quick = self.page.locator(".o_kanban_quick_create")
        expect(quick.locator("[name='team_id'] input")).to_be_visible()
        quick.locator("[name='team_id'] input").fill(self.team_names[0])
        self.page.get_by_role("option", name=self.team_names[0], exact=True).click()
        name = f"STPC E2E Quick {self.run_id}"
        quick.locator("[name='name'] input").fill(name)
        quick.get_by_role("button", name="Add", exact=True).click()
        expect(self.page.locator(".o_kanban_record").filter(has_text=name)).to_be_visible()
        created = self.call("crm.lead", "search_read", [[["name", "=", name]]], fields=["team_id", "pipeline_category_id"])[0]
        self.assertEqual(created["team_id"][0], self.team)
        self.assertEqual(created["pipeline_category_id"][0], self.category)

    def test_06_sales_mapping_is_read_only_and_backend_denies_edits(self):
        group = self.call("ir.model.data", "search_read", [[
            ["module", "=", "sales_team"], ["name", "=", "group_sale_salesman"],
        ]], fields=["res_id"])[0]["res_id"]
        password = secrets.token_urlsafe(24)
        login = f"stpc_e2e_sales_{self.run_id}"
        self.call("res.users", "create", [[{
            "name": "STPC E2E Salesperson", "login": login, "password": password,
            "group_ids": [[6, 0, [group]]], "company_id": self.company, "company_ids": [[6, 0, [self.company]]],
        }]])
        client = self.browser.new_context(base_url=self.url, viewport={"width": 1440, "height": 1000})
        try:
            session = self.authenticate(client, login, password)
            response = self.request("crm.team", "write", [[self.team], {"pipeline_category_ids": [[5, 0, 0]]}],
                                    client=client, context=session["user_context"])
            self.assertEqual(response["error"]["data"]["name"], "odoo.exceptions.AccessError")
            page = client.new_page()
            page.on("pageerror", lambda error: self.errors.append(str(error)))
            self.open_backend(page, f"crm.team/{self.team}")
            page.get_by_role("tab", name="Pipeline Categories", exact=True).click()
            expect(page.locator("[name='pipeline_category_ids']")).to_contain_text(self.category_names[0])
            expect(page.locator("[name='pipeline_category_ids'] input")).to_have_count(0)
            page.screenshot(path=str(self.output / "STPC08-sales-read-only.png"), full_page=True)
        finally:
            client.close()

    def test_07_compatibility_report_is_read_only(self):
        # The base ORM snapshot/upgrade test supplies genuine legacy mismatches;
        # this browser case checks the report view contract without bypassing ORM.
        action_id = self.call("ir.model.data", "search_read", [[
            ["module", "=", "kpability_sales_team_pipeline_categories"],
            ["name", "=", "action_pipeline_team_compatibility"],
        ]], fields=["res_id"])[0]["res_id"]
        self.open_backend(self.page, f"action-{action_id}")
        expect(self.page.locator(".o_list_view")).to_be_visible()
        expect(self.page.get_by_role("button", name="New", exact=True)).to_have_count(0)
        expect(self.page.locator(".o_list_record_selector")).to_have_count(0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
