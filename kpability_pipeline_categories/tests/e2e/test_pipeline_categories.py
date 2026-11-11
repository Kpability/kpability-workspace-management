"""Opt-in Playwright checks against a disposable, localhost Enterprise database.

Requires playwright and an installed Chromium browser. Creates synthetic records
and leaves them available for inspection; never point this at a client database.
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


class PipelineCategoryBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("ODOO_E2E_URL", "http://127.0.0.1:18020")
        cls.database = os.environ.get("ODOO_E2E_DATABASE", "kpability_pipeline_dev")
        if (
            os.environ.get("ODOO_E2E_ALLOW_WRITES") != "1"
            or urlparse(cls.url).hostname not in {"127.0.0.1", "localhost", "::1"}
            or not cls.database.startswith("kpability_pipeline_")
        ):
            raise unittest.SkipTest("Explicit opt-in and a disposable localhost kpability_pipeline_* database are required.")
        cls.password = os.environ["ODOO_E2E_PASSWORD"]
        cls.login = os.environ.get("ODOO_E2E_LOGIN", "admin")
        cls.run_id = datetime.now(timezone.utc).strftime("%m%d%H%M%S")
        sequence = int(cls.run_id)
        cls.output = Path(os.environ.get("ODOO_E2E_ARTIFACTS", "/tmp/opencode/kpability-pipeline-e2e")) / cls.run_id
        cls.output.mkdir(parents=True, exist_ok=True)
        cls.playwright = sync_playwright().start()
        cls.browser = cls.playwright.chromium.launch(headless=True)
        cls.context = cls.browser.new_context(
            base_url=cls.url, viewport={"width": 1440, "height": 1000},
            record_video_dir=str(cls.output / "video"),
            record_video_size={"width": 1440, "height": 1000},
        )
        session = cls.authenticate(cls.context, cls.login, cls.password)
        assert session["server_version"].startswith("20.0+e"), "Odoo 20 Enterprise is required"
        cls.uid = session["uid"]
        cls.company_id = session["user_companies"]["current_company"]
        cls.user_context = session["user_context"]
        installed = cls.call("ir.module.module", "search_read", [[
            ["name", "in", ["web_enterprise", "crm_enterprise", "kpability_pipeline_categories"]],
            ["state", "=", "installed"],
        ]], fields=["name"])
        assert len(installed) == 3, "Enterprise CRM and the category add-on must be installed"
        cls.stages = cls.call("crm.stage", "create", [[
            {"name": f"E2E Intake {cls.run_id}", "sequence": sequence},
            {"name": f"E2E Qualification {cls.run_id}", "sequence": sequence + 1},
            {"name": f"E2E Review {cls.run_id}", "sequence": sequence + 2},
            {"name": f"E2E Won {cls.run_id}", "sequence": sequence + 3, "is_won": True},
        ]])
        cls.category_name = f"E2E New Business {cls.run_id}"
        cls.renewal_name = f"E2E Renewals {cls.run_id}"
        cls.categories = cls.call("crm.pipeline.category", "create", [[
            {
                "s_name": cls.category_name, "company_id": cls.company_id,
                "stage_ids": [[6, 0, [cls.stages[0], cls.stages[1], cls.stages[3]]]],
            },
            {
                "s_name": cls.renewal_name, "company_id": False,
                "stage_ids": [[6, 0, [cls.stages[0], cls.stages[2], cls.stages[3]]]],
            },
        ]])
        cls.lead_name = f"E2E New Business Deal {cls.run_id}"
        cls.leads = cls.call("crm.lead", "create", [[
            cls.lead_values(cls.lead_name, cls.categories[0], cls.stages[1]),
            cls.lead_values(f"E2E Renewal Deal {cls.run_id}", cls.categories[1], cls.stages[2]),
        ]])
        cls.artifact_info = {
            "server_version": session["server_version"], "database": cls.database,
            "run_id": cls.run_id, "categories": cls.categories, "stages": cls.stages,
            "leads": cls.leads, "browser": cls.browser.version,
        }
        (cls.output / "dataset.json").write_text(json.dumps(cls.artifact_info, indent=2))

    @classmethod
    def authenticate(cls, context, login, password):
        payload = context.request.post("/web/session/authenticate", data={
            "jsonrpc": "2.0", "method": "call", "params": {
                "db": cls.database, "login": login, "password": password,
            },
        }).json()
        if payload.get("error"):
            raise RuntimeError(payload["error"]["data"]["message"])
        return payload["result"]

    @classmethod
    def request(cls, model, method, args, *, client=None, **kwargs):
        kwargs.setdefault("context", cls.user_context)
        return (client or cls.context).request.post("/web/dataset/call_kw", data={
            "jsonrpc": "2.0", "method": "call", "params": {
                "model": model, "method": method, "args": args, "kwargs": kwargs,
            },
        }).json()

    @classmethod
    def call(cls, model, method, args, **kwargs):
        payload = cls.request(model, method, args, **kwargs)
        if payload.get("error"):
            raise RuntimeError(payload["error"]["data"]["message"])
        return payload["result"]

    @classmethod
    def lead_values(cls, name, category_id, stage_id):
        return {
            "name": name, "type": "opportunity", "user_id": cls.uid,
            "company_id": cls.company_id, "pipeline_category_id": category_id,
            "stage_id": stage_id, "expected_revenue": 100,
        }

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
        self.assertEqual(self.errors, [], "Unexpected browser JavaScript errors")

    @classmethod
    def tearDownClass(cls):
        cls.context.close()
        cls.browser.close()
        cls.playwright.stop()
        print(f"Browser evidence: {cls.output}")

    def open_record(self, model, record_id):
        self.page.goto(f"/odoo/{model}/{record_id}", wait_until="domcontentloaded")
        self.page.locator(".o_form_view").wait_for()

    def test_01_category_configuration(self):
        self.open_record("crm.pipeline.category", self.categories[0])
        expect(self.page.locator("[name='s_name'] input")).to_have_value(self.category_name)
        expect(self.page.locator("[name='stage_ids']")).to_contain_text(f"E2E Qualification {self.run_id}")
        expect(self.page.locator("[name='stage_ids']")).not_to_contain_text(f"E2E Review {self.run_id}")

    def test_02_scoped_board_columns_and_reload(self):
        self.open_record("crm.pipeline.category", self.categories[0])
        self.page.get_by_role("button", name="Open Pipeline", exact=True).click()
        columns = self.page.locator(".o_kanban_header .o_column_title")
        expect(columns).to_have_count(3)
        expect(self.page.locator(".o_kanban_renderer")).to_contain_text(self.lead_name)
        expect(self.page.locator(".o_kanban_renderer")).not_to_contain_text(f"E2E Renewal Deal {self.run_id}")
        expected = {f"E2E {name} {self.run_id}" for name in ("Intake", "Qualification", "Won")}
        self.assertEqual({text.strip() for text in columns.all_text_contents()}, expected)
        self.page.reload(wait_until="domcontentloaded")
        expect(columns).to_have_count(3)
        self.assertEqual({text.strip() for text in columns.all_text_contents()}, expected)

    def test_03_dirty_form_discard_and_explicit_save(self):
        lead_id = self.call("crm.lead", "create", [[
            self.lead_values(f"E2E Draft Deal {self.run_id}", self.categories[0], self.stages[1]),
        ]])[0]
        self.open_record("crm.lead", lead_id)
        revenue = self.page.locator("[name='expected_revenue'] input").first
        revenue.fill("4321")
        category = self.page.locator("[name='pipeline_category_id'] input").first
        category.fill(self.renewal_name)
        self.page.get_by_role("option", name=self.renewal_name, exact=True).click()
        persisted = self.call("crm.lead", "read", [[lead_id], ["expected_revenue", "pipeline_category_id", "stage_id"]])[0]
        self.assertEqual(persisted["expected_revenue"], 100)
        self.assertEqual(persisted["stage_id"][0], self.stages[1])
        self.page.get_by_role("button", name="Discard all changes", exact=True).click()
        expect(category).to_have_value(self.category_name)
        revenue.fill("4321")
        self.page.get_by_role("button", name="Save manually", exact=True).click()
        expect(self.page.locator(".o_form_status_indicator_buttons")).to_have_class(re.compile("invisible"))
        self.page.reload(wait_until="domcontentloaded")
        expect(revenue).to_have_value(re.compile("4.?321"))
        persisted = self.call("crm.lead", "read", [[lead_id], ["expected_revenue", "pipeline_category_id"]])[0]
        self.assertEqual(persisted["expected_revenue"], 4321)
        self.assertEqual(persisted["pipeline_category_id"][0], self.categories[0])

        category.fill(self.renewal_name)
        self.page.get_by_role("option", name=self.renewal_name, exact=True).click()
        self.page.locator(f"[name='stage_id'] button[data-value='{self.stages[2]}']").click()
        self.page.get_by_role("button", name="Save manually", exact=True).click()
        expect(self.page.locator(".o_form_status_indicator_buttons")).to_have_class(re.compile("invisible"))
        self.page.reload(wait_until="domcontentloaded")
        expect(category).to_have_value(self.renewal_name)
        persisted = self.call("crm.lead", "read", [[lead_id], ["expected_revenue", "pipeline_category_id", "stage_id"]])[0]
        self.assertEqual(persisted["expected_revenue"], 4321)
        self.assertEqual(persisted["pipeline_category_id"][0], self.categories[1])
        self.assertEqual(persisted["stage_id"][0], self.stages[2])

    def test_04_invalid_save_and_rpc_cannot_bypass_mapping(self):
        self.open_record("crm.lead", self.leads[0])
        category = self.page.locator("[name='pipeline_category_id'] input").first
        category.fill(self.renewal_name)
        self.page.get_by_role("option", name=self.renewal_name, exact=True).click()
        self.page.get_by_role("button", name="Save manually", exact=True).click()
        expect(self.page.get_by_role("dialog")).to_contain_text("Choose a stage mapped to the selected pipeline category")
        self.page.screenshot(path=str(self.output / "PC-04-invalid-save.png"), full_page=True)
        payload = self.request("crm.lead", "write", [[self.leads[0]], {"stage_id": self.stages[2]}])
        self.assertEqual(payload["error"]["data"]["name"], "odoo.exceptions.ValidationError")
        persisted = self.call("crm.lead", "read", [[self.leads[0]], ["pipeline_category_id", "stage_id"]])[0]
        self.assertEqual(persisted["pipeline_category_id"][0], self.categories[0])
        self.assertEqual(persisted["stage_id"][0], self.stages[1])

    def test_05_sales_category_is_read_only(self):
        group = self.call("ir.model.data", "search_read", [[
            ["module", "=", "sales_team"], ["name", "=", "group_sale_salesman"],
        ]], fields=["res_id"])[0]["res_id"]
        password = secrets.token_urlsafe(24)
        login = f"pc_e2e_sales_{self.run_id}"
        self.call("res.users", "create", [[{
            "name": f"E2E Sales {self.run_id}", "login": login, "password": password,
            "email": f"{login}@example.com", "company_id": self.company_id,
            "company_ids": [[6, 0, [self.company_id]]], "group_ids": [[6, 0, [group]]],
        }]])
        context = self.browser.new_context(base_url=self.url, viewport={"width": 1440, "height": 1000})
        try:
            self.authenticate(context, login, password)
            page = context.new_page()
            page.goto(f"/odoo/crm.pipeline.category/{self.categories[0]}", wait_until="domcontentloaded")
            expect(page.locator(".o_form_view [name='s_name']")).to_contain_text(self.category_name)
            expect(page.locator(".o_form_view [name='s_name'] input")).to_have_count(0)
            expect(page.get_by_role("button", name="Open Pipeline", exact=True)).to_be_visible()
            page.screenshot(path=str(self.output / "PC-07-sales-read-only.png"), full_page=True)
            payload = self.request("crm.pipeline.category", "write", [self.categories[:1], {"s_description": "Denied"}], client=context)
            self.assertEqual(payload["error"]["data"]["name"], "odoo.exceptions.AccessError")
        finally:
            context.close()

    def test_06_scoped_quick_create(self):
        self.open_record("crm.pipeline.category", self.categories[0])
        self.page.get_by_role("button", name="Open Pipeline", exact=True).click()
        group = self.page.locator(".o_kanban_group").first
        group.locator(".o_kanban_quick_add").click()
        quick = group.locator(".o_kanban_quick_create")
        expect(quick.locator("[name='pipeline_category_id']")).to_contain_text(self.category_name)
        name = f"E2E Quick Deal {self.run_id}"
        quick.locator("[name='name'] input").fill(name)
        quick.get_by_role("button", name="Add", exact=True).click()
        expect(group).to_contain_text(name)
        record = self.call("crm.lead", "search_read", [[["name", "=", name]]], fields=["pipeline_category_id", "stage_id"])[0]
        self.assertEqual(record["pipeline_category_id"][0], self.categories[0])
        self.assertEqual(record["stage_id"][0], self.stages[0])

    def test_07_mixed_board_rejects_incompatible_drag(self):
        self.page.goto("/odoo/crm", wait_until="domcontentloaded")
        source = self.page.locator(".o_kanban_record").filter(has_text=self.lead_name)
        source_group = self.page.locator(".o_kanban_group").filter(
            has=self.page.locator(".o_column_title", has_text=f"E2E Qualification {self.run_id}"),
        )
        target = self.page.locator(".o_kanban_group").filter(
            has=self.page.locator(".o_column_title", has_text=f"E2E Review {self.run_id}"),
        )
        for group in (source_group, target):
            group.wait_for()
            unfold = group.get_by_role("button", name=re.compile("Unfold"))
            if unfold.count():
                unfold.click()
                group.evaluate("""async (el) => {
                    const animations = el.getAnimations({subtree: true}).filter(
                        animation => Number.isFinite(animation.effect.getTiming().iterations)
                    );
                    await Promise.all(animations.map(animation => animation.finished.catch(() => {})));
                }""")
        source.wait_for()
        # Move the native horizontal viewport, not application state. Keep the
        # two adjacent columns visible before performing a real mouse drag.
        source.evaluate("""(el) => {
            const content = el.closest('.o_content');
            content.scrollLeft += el.getBoundingClientRect().left
                - content.getBoundingClientRect().left - 30;
        }""")
        target.scroll_into_view_if_needed()
        expect(source).to_be_in_viewport()
        expect(target).to_be_in_viewport(ratio=0.9)
        start = source.bounding_box()
        self.page.mouse.move(start["x"] + 80, start["y"] + 25)
        self.page.mouse.down()
        self.page.mouse.move(start["x"] + 90, start["y"] + 35, steps=5)
        # Unfolding/drag placeholders can change the geometry. Re-target after
        # drag activation, and require the actual RPC to name the intended stage.
        for _ in range(2):
            end = target.bounding_box()
            self.page.mouse.move(end["x"] + end["width"] / 2, end["y"] + 160, steps=15)

        def writes_target_stage(response):
            params = (response.request.post_data_json or {}).get("params", {})
            args = params.get("args", [])
            return (
                params.get("model") == "crm.lead"
                and params.get("method") in {"write", "web_save"}
                and len(args) > 1
                and self.leads[0] in args[0]
                and args[1].get("stage_id") == self.stages[2]
            )

        with self.page.expect_response(writes_target_stage):
            self.page.mouse.up()
        expect(self.page.get_by_role("dialog")).to_contain_text("Choose a stage mapped to the selected pipeline category")
        persisted = self.call("crm.lead", "read", [self.leads[:1], ["pipeline_category_id", "stage_id"]])[0]
        self.assertEqual(persisted["pipeline_category_id"][0], self.categories[0])
        self.assertEqual(persisted["stage_id"][0], self.stages[1])

    def test_08_native_group_by_category(self):
        self.page.goto("/odoo/crm", wait_until="domcontentloaded")
        self.page.locator(".o_searchview_dropdown_toggler").click()
        self.page.get_by_role("menuitemcheckbox", name="Pipeline Category", exact=True).click()
        columns = self.page.locator(".o_kanban_header .o_column_title")
        expect(columns.filter(has_text=self.category_name)).to_have_count(1)
        expect(columns.filter(has_text=self.renewal_name)).to_have_count(1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
