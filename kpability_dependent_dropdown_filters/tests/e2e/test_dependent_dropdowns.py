"""Opt-in Playwright checks; never imported by Odoo's model test loader."""

import json
import os
import re
import unittest
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright


class DependentDropdownBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("DDF_E2E_URL", "http://127.0.0.1:18043")
        if (os.environ.get("DDF_ALLOW_WRITES") != "1"
                or urlparse(cls.url).hostname not in {"127.0.0.1", "localhost", "::1"}):
            raise unittest.SkipTest("Explicit opt-in and a disposable localhost DB are required")
        root = Path("/tmp/opencode/kpability-ddf-browser")
        cls.fixture = json.loads((root / "fixture.json").read_text())
        assert cls.fixture["database"].startswith("kpability_ddf_")
        cls.credentials = json.loads((root / "credentials.json").read_text())
        cls.output = root / datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        cls.output.mkdir(exist_ok=False)
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        endpoint = os.environ.get("DDF_CDP_URL")
        if endpoint:
            parsed = urlparse(endpoint)
            if (parsed.scheme != "ws"
                    or parsed.hostname not in {"127.0.0.1", "localhost", "::1"}
                    or not parsed.path.startswith("/devtools/browser/")):
                raise ValueError("Only an explicitly supplied localhost browser CDP endpoint is supported")
            # Brave may require a fresh, user-approved debugging connection.
            cls.browser = cls.playwright.chromium.connect_over_cdp(endpoint, timeout=120000)
        else:
            cls.browser = cls.playwright.chromium.launch(headless=True)
            cls.addClassCleanup(cls.browser.close)
        cls.context = cls.browser.new_context(
            base_url=cls.url, viewport={"width": 1440, "height": 1000},
            record_video_dir=str(cls.output / "video"),
            record_video_size={"width": 1440, "height": 1000},
        )
        cls.addClassCleanup(cls.context.close)
        cls.session = cls.authenticate(cls.context, "admin", cls.credentials["admin"])
        assert cls.session["server_version"].startswith("20.0+e")
        # Repeat runs reset only this runner's explicitly identified synthetic record.
        cls.call("crm.lead", "write", [[cls.fixture["opportunity"]], {
            "name": "DDF Browser Opportunity",
            "customer_company_id": cls.fixture["customer_a"],
            "partner_id": cls.fixture["people_a"][0],
        }])
        cls.results = {"database": cls.fixture["database"], "browser": cls.browser.version,
                       "transport": "remote-debugging-cdp" if endpoint else "launched-chromium",
                       "server_version": cls.session["server_version"], "cases": []}
        cls.viewport = {"width": 1440, "height": 1000}
        if endpoint:
            probe = cls.context.new_page()
            try:
                probe.goto("/odoo", wait_until="domcontentloaded")
                cls.results["brave_verified"] = probe.evaluate(
                    "async () => Boolean(navigator.brave && await navigator.brave.isBrave())",
                )
                initial = probe.evaluate(
                    "() => ({width: visualViewport.width, height: visualViewport.height})",
                )
                # Attached profiles can inherit page zoom. Resize only our
                # pages' viewport; never change the user's zoom settings.
                cls.viewport = {
                    key: round(value * value / initial[key]) for key, value in cls.viewport.items()
                }
                probe.set_viewport_size(cls.viewport)
                cls.results["initial_effective_viewport"] = initial
                cls.results["effective_viewport"] = probe.evaluate(
                    "() => ({width: innerWidth, height: innerHeight, device_pixel_ratio: devicePixelRatio})",
                )
            finally:
                probe.close()

    @classmethod
    def authenticate(cls, context, login, password):
        response = context.request.post("/web/session/authenticate", data={
            "jsonrpc": "2.0", "method": "call",
            "params": {"db": cls.fixture["database"], "login": login, "password": password},
        }).json()
        if response.get("error"):
            raise RuntimeError(response["error"]["data"]["message"])
        return response["result"]

    @classmethod
    def request(cls, model, method, args, *, context=None, session=None, **kwargs):
        kwargs.setdefault("context", (session or cls.session)["user_context"])
        return (context or cls.context).request.post("/web/dataset/call_kw", data={
            "jsonrpc": "2.0", "method": "call",
            "params": {"model": model, "method": method, "args": args, "kwargs": kwargs},
        }).json()

    @classmethod
    def call(cls, model, method, args, **kwargs):
        response = cls.request(model, method, args, **kwargs)
        if response.get("error"):
            raise RuntimeError(response["error"]["data"]["message"])
        return response["result"]

    def setUp(self):
        self.page = self.context.new_page()
        self.page.set_viewport_size(self.viewport)
        self.page.set_default_timeout(20000)
        self.errors = []
        self.extra_videos = []
        self.console_errors = []
        self.failed_requests = []
        self.observe(self.page)

    def observe(self, page):
        page.on("pageerror", lambda error: self.errors.append(str(error)))
        page.on("console", lambda message: (
            self.console_errors.append(message.text) if message.type == "error" else None
        ))
        page.on("requestfailed", lambda request: self.failed_requests.append({
            "path": urlparse(request.url).path, "failure": request.failure,
        }))

    def tearDown(self):
        viewport = self.page.evaluate(
            "() => ({width: innerWidth, height: innerHeight, device_pixel_ratio: devicePixelRatio})",
        )
        self.page.screenshot(path=str(self.output / f"{self._testMethodName}.png"), full_page=True)
        self.page.close()
        videos = [self.page.video.path(), *self.extra_videos]
        failures = self._outcome.result.errors + self._outcome.result.failures
        self.results["cases"].append({
            "case": self._testMethodName, "javascript_errors": self.errors,
            "console_errors": self.console_errors, "failed_requests": self.failed_requests,
            "effective_viewport": viewport,
            "status": "failed" if self.errors or any(test is self for test, _ in failures) else "passed",
            "screenshot": f"{self._testMethodName}.png",
            "videos": [str(path.relative_to(self.output)) for path in videos],
        })
        (self.output / "results.json").write_text(json.dumps(self.results, indent=2) + "\n")
        self.assertEqual(self.errors, [])

    @classmethod
    def tearDownClass(cls):
        # Class cleanups close only contexts owned by this runner, then disconnect.
        # Never send Browser.close to an attached user browser.
        print(f"Browser evidence: {cls.output}")

    def open_record(self, model, record_id):
        self.page.goto(f"/odoo/{model}/{record_id}", wait_until="domcontentloaded")
        self.page.locator(".o_form_view").wait_for()

    def contact_input(self):
        return self.page.locator("[name='partner_id'] input:visible")

    def binding_rule(self, key):
        rules = self.call("dropdown.filters", "search_read", [[
            ("id", "in", self.fixture["rules"]), ("adapter_id.s_key", "=", key),
        ]], fields=["id", "company_id", "department_id", "active"])
        self.assertEqual(len(rules), 1)
        return rules[0]

    def test_00_configuration_is_record_maintained_and_company_scoped(self):
        rules = self.call("dropdown.filters", "search_read", [[
            ("id", "in", self.fixture["rules"]),
            ("adapter_id.s_key", "=", "crm_sales_department"),
        ]], fields=["id", "company_id", "department_id", "active"])
        self.assertEqual(len(rules), 1)
        self.assertEqual(rules[0]["company_id"][0], self.fixture["company"])
        self.assertTrue(rules[0]["active"])
        self.open_record("dropdown.filters", rules[0]["id"])
        expect(self.page.locator("[name='adapter_id'] input")).to_have_value(
            "CRM: Department → Salesperson",
        )
        expect(self.page.locator("[name='department_id'] input")).to_have_value(
            "DDF Configured Commercial",
        )
        self.page.screenshot(path=str(self.output / "DDF01-maintained-configuration.png"), full_page=True)

    def test_01_autocomplete_search_more_and_native_lead_reuse(self):
        for key in ("opportunity", "lead"):
            self.open_record("crm.lead", self.fixture[key])
            self.contact_input().fill("DDF Browser")
            options = self.page.get_by_role("option")
            expect(options.first).to_be_visible()
            expect(self.page.get_by_role("option", name="DDF Browser B Person", exact=False)).to_have_count(0)
            self.page.get_by_role("option", name="Search More...", exact=False).click()
            dialog = self.page.get_by_role("dialog")
            expect(dialog.locator(".o_data_row")).to_have_count(12)
            expect(dialog).not_to_contain_text("DDF Browser B Person")
            expect(dialog).not_to_contain_text("DDF Browser Archived")
            self.page.screenshot(path=str(self.output / f"DDF02-{key}-search-more.png"), full_page=True)
            dialog.get_by_role("button", name="Close", exact=True).last.click()

    def test_02_stale_draft_explicit_repair_save_and_discard(self):
        self.open_record("crm.lead", self.fixture["opportunity"])
        self.page.locator("[name='name'] textarea").fill("DDF Browser unsaved name")
        parent = self.page.locator("[name='customer_company_id'] input")
        parent.fill("DDF Browser Company B")
        self.page.get_by_role("option", name="DDF Browser Company B", exact=False).click()
        expect(self.contact_input()).to_have_value("DDF Browser Company A, DDF Browser A Person 01")
        expect(self.page.locator("[name='s_dropdown_contact_hint']")).to_contain_text("no longer matches")
        self.page.screenshot(path=str(self.output / "DDF05-stale-draft-preserved.png"), full_page=True)
        self.contact_input().fill("DDF Browser B")
        self.page.get_by_role("option", name="DDF Browser B Person", exact=False).click()
        with self.page.expect_response(
            lambda response: "/web/dataset/call_kw/crm.lead/web_save" in response.url,
        ) as save:
            self.page.locator(".o_form_button_save").click()
        self.assertNotIn("error", save.value.json())
        expect(self.page.locator(".o_form_button_save")).to_be_hidden()
        saved = self.call("crm.lead", "read", [[self.fixture["opportunity"]],
                                              ["partner_id", "customer_company_id", "name"]])[0]
        self.assertEqual(saved["partner_id"][0], self.fixture["person_b"])
        self.assertEqual(saved["customer_company_id"][0], self.fixture["customer_b"])
        parent.fill("DDF Browser Company A")
        self.page.get_by_role("option", name="DDF Browser Company A", exact=False).click()
        self.page.locator(".o_form_button_cancel").click()
        expect(parent).to_have_value("DDF Browser Company B")
        persisted = self.call("crm.lead", "read", [[self.fixture["opportunity"]], ["partner_id"]])[0]
        self.assertEqual(persisted["partner_id"][0], self.fixture["person_b"])

    def test_03_contacts_reuse_and_no_creation_shortcut(self):
        self.open_record("res.partner", self.fixture["customer_a"])
        self.page.get_by_role("tab", name="Sales & Purchase", exact=True).click()
        self.page.locator("[name='primary_contact_id'] input").fill("DDF Browser")
        expect(self.page.get_by_role("option", name="DDF Browser B Person", exact=False)).to_have_count(0)
        expect(self.page.get_by_role("option", name="Search More...", exact=False)).to_be_visible()
        expect(self.page.get_by_role("option", name="Create", exact=False)).to_have_count(0)

    def test_04_ordinary_salesperson_public_hr_and_backend_denials(self):
        context = self.browser.new_context(
            base_url=self.url, viewport=self.viewport,
            record_video_dir=str(self.output / "video"),
            record_video_size={"width": 1440, "height": 1000},
        )
        page = None
        try:
            session = self.authenticate(context, "ddf_browser_sales", self.credentials["sales"])
            page = context.new_page()
            self.observe(page)
            page.goto(f"/odoo/crm.lead/{self.fixture['lead']}", wait_until="domcontentloaded")
            page.locator("[name='user_id'] input").fill("DDF")
            expect(page.get_by_role("option", name="DDF Eligible Salesperson", exact=False)).to_be_visible()
            expect(page.get_by_role("option", name="DDF Other Department", exact=False)).to_have_count(0)
            page.screenshot(path=str(self.output / "DDF07-sales-user-public-HR.png"), full_page=True)
            response = self.request(
                "hr.employee", "search_read", [[]], context=context, session=session,
                fields=["private_email"],
            )
            self.assertEqual(response["error"]["data"]["name"], "odoo.exceptions.AccessError")
            response = self.request("dropdown.filters", "write", [
                self.fixture["rules"], {"active": False},
            ], context=context, session=session)
            self.assertEqual(response["error"]["data"]["name"], "odoo.exceptions.AccessError")
            response = self.request("crm.lead", "write", [[self.fixture["lead"]], {
                "user_id": self.fixture["users"][1],
            }], context=context, session=session)
            self.assertEqual(response["error"]["data"]["name"], "odoo.exceptions.ValidationError")
            response = self.request("crm.lead", "write", [[self.fixture["lead"]], {
                "customer_company_id": self.fixture["customer_b"],
            }], context=context, session=session)
            self.assertEqual(response["error"]["data"]["name"], "odoo.exceptions.ValidationError")
        finally:
            context.close()
            if page:
                self.extra_videos.append(page.video.path())

    def test_05_missing_parent_and_empty_company_do_not_broaden_choices(self):
        empty_company = self.call("res.partner", "create", [{
            "name": "DDF Browser Empty Company", "vat": "US222222222",
            "company_id": self.fixture["company"],
        }])
        self.addCleanup(self.call, "res.partner", "unlink", [[empty_company]])
        lead = self.call("crm.lead", "create", [{
            "name": "DDF Browser Empty State", "type": "lead",
            "company_id": self.fixture["company"], "user_id": self.fixture["users"][0],
        }])
        self.addCleanup(self.call, "crm.lead", "unlink", [[lead]])
        self.open_record("crm.lead", lead)
        hint = self.page.locator("[name='s_dropdown_contact_hint']")
        expect(hint).to_contain_text("Select a saved customer company first")
        with self.page.expect_response(
            lambda response: "/web/dataset/call_kw/res.partner/web_name_search" in response.url,
        ) as choices:
            self.contact_input().fill("DDF Browser")
        self.assertEqual(choices.value.json().get("result"), [])
        expect(self.page.get_by_role("option", name=re.compile("DDF Browser [AB] Person"))).to_have_count(0)
        self.page.screenshot(path=str(self.output / "DDF04-missing-parent.png"), full_page=True)
        self.call("crm.lead", "write", [[lead], {"customer_company_id": empty_company}])
        self.open_record("crm.lead", lead)
        expect(hint).to_contain_text("No eligible records are available")
        with self.page.expect_response(
            lambda response: "/web/dataset/call_kw/res.partner/web_name_search" in response.url,
        ) as choices:
            self.contact_input().fill("DDF Browser")
        self.assertEqual(choices.value.json().get("result"), [])
        expect(self.page.get_by_role("option", name=re.compile("DDF Browser [AB] Person"))).to_have_count(0)
        self.page.screenshot(path=str(self.output / "DDF04-empty-company.png"), full_page=True)

    def test_06_department_configuration_changes_without_code(self):
        rule = self.binding_rule("crm_sales_department")
        departments = self.call("hr.department", "search_read", [[
            ("company_id", "=", self.fixture["company"]), ("name", "=", "Sales"),
        ]], fields=["id"])
        self.assertEqual(len(departments), 1)
        self.addCleanup(self.call, "dropdown.filters", "write", [[rule["id"]], {
            "department_id": rule["department_id"][0],
        }])
        self.open_record("dropdown.filters", rule["id"])
        self.page.locator("[name='department_id'] input").fill("Sales")
        self.page.get_by_role("option", name="Sales", exact=True).click()
        with self.page.expect_response(
            lambda response: "/web/dataset/call_kw/dropdown.filters/web_save" in response.url,
        ) as saved:
            self.page.locator(".o_form_button_save").click()
        self.assertNotIn("error", saved.value.json())
        self.open_record("crm.lead", self.fixture["lead"])
        expect(self.page.locator("[name='s_dropdown_salesperson_hint']")).to_contain_text("no longer matches")
        self.page.locator("[name='user_id'] input").fill("DDF")
        expect(self.page.get_by_role("option", name="DDF Other Department", exact=False)).to_be_visible()
        expect(self.page.get_by_role("option", name="DDF Eligible Salesperson", exact=False)).to_have_count(0)
        unchanged = self.call("crm.lead", "read", [[self.fixture["lead"]], ["user_id"]])[0]
        self.assertEqual(unchanged["user_id"][0], self.fixture["users"][0])
        self.page.screenshot(path=str(self.output / "DDF08-configuration-change-no-backfill.png"), full_page=True)

    def test_07_deactivation_restores_native_choices_without_rewriting_history(self):
        rule = self.binding_rule("crm_customer_contact")
        self.addCleanup(self.call, "dropdown.filters", "write", [[rule["id"]], {"active": True}])
        self.call("dropdown.filters", "write", [[rule["id"]], {"active": False}])
        lead = self.call("crm.lead", "create", [{
            "name": "DDF Browser Disabled Filter", "type": "lead",
            "company_id": self.fixture["company"], "user_id": self.fixture["users"][0],
            "customer_company_id": self.fixture["customer_a"], "partner_id": self.fixture["person_b"],
        }])
        self.addCleanup(self.call, "crm.lead", "unlink", [[lead]])
        self.open_record("crm.lead", lead)
        self.contact_input().fill("DDF Browser B")
        expect(self.page.get_by_role("option", name="DDF Browser B Person", exact=False)).to_be_visible()
        self.page.screenshot(path=str(self.output / "DDF11-inactive-native-choices.png"), full_page=True)
        self.call("dropdown.filters", "write", [[rule["id"]], {"active": True}])
        self.open_record("crm.lead", lead)
        expect(self.page.locator("[name='s_dropdown_contact_hint']")).to_contain_text("no longer matches")
        unchanged = self.call("crm.lead", "read", [[lead], ["partner_id"]])[0]
        self.assertEqual(unchanged["partner_id"][0], self.fixture["person_b"])
        self.call("crm.lead", "write", [[lead], {"name": "DDF Browser Unrelated Legacy Edit"}])

    def test_08_keyboard_selects_an_eligible_contact_without_creation(self):
        self.open_record("crm.lead", self.fixture["lead"])
        contact = self.contact_input()
        contact.fill("DDF Browser A Person 02")
        expect(self.page.get_by_role("option", name="DDF Browser A Person 02", exact=False)).to_be_visible()
        contact.press("ArrowDown")
        contact.press("ArrowUp")
        expect(self.page.get_by_role("option", selected=True)).to_contain_text("DDF Browser A Person 02")
        contact.press("Enter")
        expect(contact).to_have_value("DDF Browser Company A, DDF Browser A Person 02")
        self.page.screenshot(path=str(self.output / "DDF10-keyboard-selection.png"), full_page=True)
        self.page.locator(".o_form_button_cancel").click()
        expect(contact).to_have_value("DDF Browser Company A, DDF Browser A Person 01")

    def test_09_latest_parent_wins_while_an_older_onchange_is_in_flight(self):
        self.open_record("crm.lead", self.fixture["lead"])
        held = []
        released = []

        def is_parent_request(request, parent_id):
            data = request.post_data_json or {}
            args = data.get("params", {}).get("args", [])
            return len(args) > 1 and args[1].get("customer_company_id") == parent_id

        def hold_first_older_request(route):
            if not held and not released and is_parent_request(route.request, self.fixture["customer_b"]):
                held.append(route)
            else:
                route.continue_()

        pattern = "**/web/dataset/call_kw/crm.lead/onchange"
        self.page.route(pattern, hold_first_older_request)
        try:
            parent = self.page.locator("[name='customer_company_id'] input")
            with self.page.expect_request(lambda request: (
                request.url.endswith("/crm.lead/onchange")
                and is_parent_request(request, self.fixture["customer_b"])
            )):
                parent.fill("DDF Browser Company B")
                self.page.get_by_role("option", name="DDF Browser Company B", exact=False).click()
            self.assertEqual(len(held), 1, "The older onchange must really be held in flight")
            # Native Odoo retains its rendered value until onchange resolves;
            # do not assume an optimistic parent render while the RPC is held.
            parent.fill("DDF Browser Company A")
            self.page.get_by_role("option", name="DDF Browser Company A", exact=False).click()
            expect(parent).to_have_value("DDF Browser Company A")
            self.page.screenshot(path=str(self.output / "DDF05-new-parent-old-request-pending.png"), full_page=True)
            with self.page.expect_response(lambda response: (
                response.url.endswith("/crm.lead/onchange")
                and is_parent_request(response.request, self.fixture["customer_a"])
            )) as latest:
                released.append(held.pop())
                released[0].continue_()
            self.assertNotIn("error", latest.value.json())
            latest.value.finished()
            # A received RPC is not yet an OWL render. Wait for rendering,
            # rather than typing into an input about to be replaced.
            self.page.evaluate(
                "() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)))",
            )
            with self.page.expect_response(
                lambda response: "/web/dataset/call_kw/res.partner/web_name_search" in response.url,
            ) as choices:
                self.contact_input().fill("DDF Browser")
            response = choices.value
            self.assertIn(
                ["parent_id", "=", self.fixture["customer_a"]],
                response.request.post_data_json["params"]["kwargs"]["domain"],
            )
            matches = response.json().get("result")
            self.assertTrue(matches)
            self.assertTrue({record["id"] for record in matches}.issubset(self.fixture["people_a"]))
            expect(self.page.get_by_role("option", name="DDF Browser A Person 01", exact=False)).to_be_visible()
            expect(self.page.get_by_role("option", name="DDF Browser B Person", exact=False)).to_have_count(0)
            expect(parent).to_have_value("DDF Browser Company A")
            self.page.screenshot(path=str(self.output / "DDF05-latest-parent-filter.png"), full_page=True)
        finally:
            for route in held:
                route.continue_()
            self.page.unroute(pattern, hold_first_older_request)


if __name__ == "__main__":
    unittest.main(verbosity=2)
