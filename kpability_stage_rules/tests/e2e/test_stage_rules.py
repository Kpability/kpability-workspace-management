"""Opt-in browser proof on a disposable localhost Odoo 20 database."""

import os
import re
import secrets
import unittest
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import expect, sync_playwright


class StageRulesBrowserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.url = os.environ.get("ODOO_E2E_URL", "http://127.0.0.1:18031")
        cls.database = os.environ.get("ODOO_E2E_DATABASE", "")
        cdp_url = os.environ.get("ODOO_E2E_CDP_URL")
        if (
            os.environ.get("ODOO_E2E_ALLOW_WRITES") != "1"
            or urlparse(cls.url).hostname not in {"127.0.0.1", "localhost", "::1"}
            or not cls.database.startswith("kpability_stage_rules_")
            or (cdp_url and urlparse(cdp_url).hostname not in {"127.0.0.1", "localhost", "::1"})
        ):
            raise unittest.SkipTest("Explicit opt-in and a disposable localhost stage rules database are required")
        cls.run_id = secrets.token_hex(3)
        cls.output = Path(os.environ.get("ODOO_E2E_ARTIFACTS", "/tmp/opencode/kpability-stage-rules-browser")) / cls.run_id
        cls.output.mkdir(parents=True)
        cls.playwright = sync_playwright().start()
        cls.addClassCleanup(cls.playwright.stop)
        if cdp_url:
            cls.browser = cls.playwright.chromium.connect_over_cdp(cdp_url)
        else:
            cls.browser = cls.playwright.chromium.launch()
            cls.addClassCleanup(cls.browser.close)
        cls.manager = cls.new_context(width=1440)
        session = cls.authenticate(
            cls.manager, os.environ.get("ODOO_E2E_LOGIN", "admin"), os.environ["ODOO_E2E_PASSWORD"],
        )
        assert session["server_version"].startswith("20.0"), session["server_version"]
        print(f'Odoo {session["server_version"]}, Chromium {cls.browser.version}. Evidence: {cls.output}')
        cls.company = session["user_companies"]["current_company"]
        cls.user = session["uid"]
        has_tours = cls.installed("web_tour")
        if has_tours:
            [preferences] = cls.call("res.users", "read", [[cls.user], ["tour_enabled"]])
            cls.call("res.users", "write", [[cls.user], {"tour_enabled": False}])
            cls.addClassCleanup(
                cls.call, "res.users", "write", [[cls.user], {"tour_enabled": preferences["tour_enabled"]}],
            )
        cls.uses_categories = cls.installed("kpability_pipeline_categories")
        cls.uses_won_reasons = cls.installed("crm_stage_reasons")
        cls.team = cls.call("crm.team", "create", [{
            "name": f"Stage Rules Team {cls.run_id}", "company_id": cls.company,
        }])
        [first_global_stage] = cls.call(
            "crm.stage", "search_read", [[["team_ids", "=", False]]],
            fields=["sequence"], order="sequence", limit=1,
        ) or [{"sequence": 0}]
        first_sequence = first_global_stage["sequence"] - 6
        cls.stage_names = [f"{name} {cls.run_id}" for name in ("Intake", "Qualification", "Review")]
        cls.intake, cls.qualification, cls.review = cls.call("crm.stage", "create", [[
            {"name": name, "sequence": sequence, "team_ids": [[6, 0, [cls.team]]]}
            for sequence, name in enumerate(cls.stage_names, start=first_sequence)
        ]])
        cls.native_names = [f"{name} {cls.run_id}" for name in ("Unconfigured", "Unconfigured next")]
        cls.native_stage, cls.native_next, cls.conflict_stage = cls.call("crm.stage", "create", [[
            {"name": name, "sequence": sequence, "team_ids": [[6, 0, [cls.team]]],
             "fold": name not in cls.native_names}
            for sequence, name in enumerate(
                [*cls.native_names, f"Conflict {cls.run_id}"], start=first_sequence + 3,
            )
        ]])
        category_stages = [
            cls.intake, cls.qualification, cls.review, cls.native_stage, cls.native_next, cls.conflict_stage,
        ]
        cls.conditions_stage, cls.native_modifiers_stage = cls.call("crm.stage", "create", [[
            {"name": f"{name} {cls.run_id}", "fold": True, "team_ids": [[6, 0, [cls.team]]]}
            for name in ("Independent conditions", "Native modifiers")
        ]])
        category_stages.extend([cls.conditions_stage, cls.native_modifiers_stage])
        cls.custom_field = f"x_stage_rules_review_{cls.run_id}"
        cls.custom_label = f"Review Notes {cls.run_id}"
        cls.picker_field = f"x_stage_rules_picker_{cls.run_id}"
        cls.picker_label = f"Approval Notes {cls.run_id}"
        cls.call("ir.model.fields", "create", [[
            {"name": name, "field_description": label, "model_id": cls.ref("crm.model_crm_lead"), "ttype": "char"}
            for name, label in ((cls.custom_field, cls.custom_label), (cls.picker_field, cls.picker_label))
        ]])
        fixture_view = cls.call("ir.ui.view", "create", [{
            "name": f"stage.rules.browser.fixture.{cls.run_id}",
            "model": "crm.lead",
            "inherit_id": cls.ref("crm.crm_lead_view_form"),
            "arch": (
                '<xpath expr="//notebook" position="before"><group>'
                f"""<field name="{cls.custom_field}" required="stage_id == {cls.native_modifiers_stage} and priority == '3'" readonly="priority == '2'"/>"""
                f'<label for="{cls.picker_field}_instance"/>'
                f'<field name="{cls.picker_field}" id="{cls.picker_field}_instance" nolabel="1"/>'
                '</group></xpath>'
            ),
        }])
        cls.addClassCleanup(cls.call, "ir.ui.view", "unlink", [[fixture_view]])
        cls.call("stage.rules.field", "create", [{"s_field_name": cls.custom_field}])
        if cls.uses_won_reasons:
            cls.won_stage = cls.call("crm.stage", "create", [{
                "name": f"Won {cls.run_id}", "is_won": True, "fold": True, "sequence": 100,
                "team_ids": [[6, 0, [cls.team]]],
            }])
            cls.won_reason_name = f"Selected proposal {cls.run_id}"
            cls.won_reason = cls.call("crm.won.reason", "create", [{
                "s_name": cls.won_reason_name, "stage_ids": [[6, 0, [cls.qualification]]],
            }])
            category_stages.append(cls.won_stage)
        cls.campaign_name = f"Stage Rules Test Campaign {cls.run_id}"
        cls.campaign = cls.call("utm.campaign", "create", [{"name": cls.campaign_name}])
        cls.medium_name = f"Stage Rules Medium {cls.run_id}"
        cls.medium = cls.call("utm.medium", "create", [{"name": cls.medium_name}])
        cls.source_name = f"Stage Rules Source {cls.run_id}"
        cls.source = cls.call("utm.source", "create", [{"name": cls.source_name}])
        cls.group = cls.ref("sales_team.group_sale_salesman")
        cls.manager_group = cls.ref("sales_team.group_sale_manager")
        cls.other_group = cls.call("res.groups", "create", [{"name": f"Stage Rules Group {cls.run_id}"}])
        cls.rep_login = f"stage_rules_rep_{cls.run_id}"
        cls.rep_password = secrets.token_urlsafe()
        cls.rep = cls.call("res.users", "create", [{
            "name": f"Stage Rules Representative {cls.run_id}",
            "login": cls.rep_login, "password": cls.rep_password, "company_id": cls.company,
            "company_ids": [[6, 0, [cls.company]]],
            "group_ids": [[6, 0, [cls.group]]],
            **({"tour_enabled": False} if has_tours else {}),
        }])
        cls.category = False
        if cls.uses_categories:
            cls.category = cls.call("crm.pipeline.category", "create", [{
                "s_name": f"Stage Rules Category {cls.run_id}", "company_id": cls.company,
                "stage_ids": [[6, 0, category_stages]],
            }])
        cls.call("stage.rules", "create", [[
            cls.rule("Keep referral for later", cls.intake, "referred", e_visibility="hidden"),
            cls.rule("Show referral with campaign", cls.qualification, "referred",
                     e_visibility="when", s_visibility_domain="[('campaign_id', '!=', False)]"),
            cls.rule("Require date for high priority", cls.qualification, "date_deadline",
                     e_required="when", s_required_domain="[('priority', '=', '3')]"),
            cls.rule("Keep campaign for managers", cls.qualification, "campaign_id",
                     e_enabled="disabled", group_ids=[[6, 0, [cls.manager_group, cls.other_group]]]),
            cls.rule("Edit referral with campaign", cls.review, "referred",
                     e_enabled="when", s_enabled_domain="[('campaign_id', '!=', False)]"),
            cls.rule("Require a closing date", cls.conflict_stage, "date_deadline", e_required="always"),
            cls.rule("Hide closing date for managers", cls.conflict_stage, "date_deadline",
                     e_visibility="hidden", group_ids=[[6, 0, [cls.manager_group]]]),
            cls.rule("Independent behaviors", cls.conditions_stage, ["referred", cls.custom_field],
                     e_visibility="when",
                     s_visibility_domain=f"[('campaign_id', 'in', [{cls.campaign}]), ('priority', '!=', '3')]",
                     e_enabled="when", s_enabled_domain="[('medium_id', '!=', False)]",
                     e_required="when", s_required_domain="[('source_id', '!=', False)]"),
            cls.rule("Native modifiers still apply", cls.native_modifiers_stage, cls.custom_field,
                     e_visibility="when", s_visibility_domain="[('campaign_id', '!=', False)]",
                     e_enabled="when", s_enabled_domain="[('campaign_id', '!=', False)]"),
        ]])

    @classmethod
    def new_context(cls, *, width):
        context = cls.browser.new_context(base_url=cls.url, viewport={"width": width, "height": 1000})
        cls.addClassCleanup(context.close)
        return context

    @classmethod
    def rpc(cls, client, path, params):
        payload = client.request.post(path, data={
            "jsonrpc": "2.0", "method": "call", "params": params,
        }).json()
        if "error" in payload:
            raise RuntimeError(payload["error"]["data"]["message"])
        return payload["result"]

    @classmethod
    def authenticate(cls, client, login, password):
        return cls.rpc(client, "/web/session/authenticate", {
            "db": cls.database, "login": login, "password": password,
        })

    @classmethod
    def call(cls, model, method, args, **kwargs):
        return cls.rpc(cls.manager, "/web/dataset/call_kw", {
            "model": model, "method": method, "args": args, "kwargs": kwargs,
        })

    @classmethod
    def ref(cls, xml_id):
        module, name = xml_id.split(".")
        return cls.call("ir.model.data", "search_read", [[["module", "=", module], ["name", "=", name]]],
                        fields=["res_id"])[0]["res_id"]

    @classmethod
    def installed(cls, module):
        return bool(cls.call("ir.module.module", "search_count", [[
            ["name", "=", module], ["state", "=", "installed"],
        ]]))

    @classmethod
    def rule(cls, name, stage, field_name, **overrides):
        targets = field_name if isinstance(field_name, list) else [field_name]
        ids = [
            cls.call("stage.rules.field", "search_read", [[["s_field_name", "=", field]]], fields=["id"])[0]["id"]
            for field in targets
        ]
        stages = stage if isinstance(stage, list) else [stage]
        return {
            "s_name": name, "active": True, "company_id": cls.company, "stage_ids": [[6, 0, stages]],
            "target_field_ids": [[6, 0, ids]], **overrides,
        }

    def opportunity(self, stage, **overrides):
        values = {
            "name": f"Stage Rules Opportunity {self.run_id}", "type": "opportunity",
            "company_id": self.company, "team_id": self.team,
            "user_id": self.user, "stage_id": stage,
            self.custom_field: "Existing note", **overrides,
        }
        if self.category:
            values["pipeline_category_id"] = self.category
        return self.call("crm.lead", "create", [values])

    def current(self, lead, *fields):
        return self.call("crm.lead", "read", [[lead], list(fields)])[0]

    def open(self, model, record, *, context=None):
        page = (context or self.manager).new_page()
        page.set_default_timeout(10000)
        self.addCleanup(page.close)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        self.addCleanup(self.assertEqual, errors, [], "Unexpected browser errors")
        self.addCleanup(self.report_browser_dialog, page)
        page.goto(f"/odoo/{model}/{record}", wait_until="domcontentloaded")
        expect(page.locator(".o_form_view")).to_be_visible(timeout=35000)
        return page

    def report_browser_dialog(self, page):
        details = page.get_by_text("See technical details", exact=False).first
        if details.is_visible():
            details.click()
            self.fail(page.get_by_role("dialog").last.inner_text())

    def close_date(self, page):
        return page.locator(".o_field_widget[name='date_deadline'] input")

    def stage(self, page, index):
        self.click_stage(page, self.stage_names[index])

    def expect_selected_stage(self, page, name):
        statusbar = page.get_by_role("radiogroup", name="Statusbar")
        selected = statusbar.get_by_role("radio", checked=True)
        expect(selected).to_have_accessible_name(re.compile(rf"^{re.escape(name)}(?:\s|$)"))

    def click_stage(self, page, name):
        statusbar = page.get_by_role("radiogroup", name="Statusbar")
        expect(statusbar).to_be_visible()
        inline_stage = statusbar.get_by_role("radio", name=name, exact=True)
        if inline_stage.is_visible():
            inline_stage.click()
            return
        # Longer stage lists can move the next stage into a native overflow menu.
        menu = page.locator(".o-dropdown--menu:visible")
        for toggle in statusbar.locator("button.dropdown-toggle:visible").all():
            toggle.click()
            expect(menu).to_be_visible()
            menu_stage = menu.get_by_text(name, exact=True)
            if menu_stage.is_visible():
                menu_stage.click()
                return
            toggle.click()
        self.fail(f"Stage not available in the native statusbar: {name}")

    def open_choices(self, page, field_name):
        page.locator(f".o_field_widget[name='{field_name}'] .o_select_menu_toggler").click()
        return page.locator(".o_field_selection_menu").get_by_role("menuitem")

    def choose(self, page, field_name, label):
        self.open_choices(page, field_name).filter(has_text=re.compile(f"^{label}$")).click()

    def capture(self, page, name):
        page.screenshot(path=str(self.output / f"{name}.png"), full_page=True, animations="disabled")

    def test_apps_description_shows_only_setup(self):
        [module] = self.call("ir.module.module", "search_read", [[
            ["name", "=", "kpability_stage_rules"],
        ]], fields=["id"])
        page = self.open("ir.module.module", module["id"])
        description = page.locator(".o_field_widget[name='description_html']")
        expect(description.get_by_text("Configure what people see", exact=False)).to_be_visible()
        expect(description.locator("li")).to_have_count(4)
        expect(description).not_to_contain_text("# Stage Rules")
        expect(description).not_to_contain_text("For example")
        expect(description).not_to_contain_text("Stage Rules development and testing")
        self.capture(page, "10-apps-description-setup-only")

    def test_stage_preview_required_save_discard_and_native_won(self):
        lead = self.opportunity(self.intake, priority="3", campaign_id=self.campaign)
        page = self.open("crm.lead", lead)
        page.get_by_role("tab", name="Extra Info", exact=True).click()
        expect(page.locator(".o_field_widget[name='referred']")).to_be_hidden()
        self.stage(page, 1)
        expect(page.locator(".o_field_widget[name='referred']")).to_be_visible()
        expect(page.locator(".o_field_widget[name='campaign_id'] input")).to_be_hidden()
        expect(page.locator(".o_form_button_save").first).to_be_visible()
        self.assertEqual(self.current(lead, "stage_id")["stage_id"][0], self.intake)
        page.get_by_role("button", name="Won", exact=True).click()
        expect(page.get_by_text("Save or discard the stage change before continuing.")).to_be_visible()
        expect(page.get_by_role("dialog")).to_have_count(0)
        page.locator(".o_form_button_save").first.click()
        expect(page.locator(".o_field_invalid[name='date_deadline']")).to_be_visible()
        self.assertEqual(self.current(lead, "stage_id")["stage_id"][0], self.intake)
        self.capture(page, "01-required-date-keeps-stage-in-draft")
        warning = page.locator(".o_notification").filter(has_text="Save or discard the stage change")
        if warning.is_visible():
            warning.get_by_role("button", name="Close").click()
        page.locator(".o_form_button_cancel").first.click()
        expect(page.locator(".o_field_widget[name='referred']")).to_be_hidden()
        self.expect_selected_stage(page, self.stage_names[0])
        self.assertEqual(self.current(lead, "stage_id")["stage_id"][0], self.intake)
        self.capture(page, "01b-discard-restores-original-stage")
        self.stage(page, 1)
        self.close_date(page).fill("12/18/2026")
        self.close_date(page).press("Tab")
        with page.expect_response(re.compile(r"/web/dataset/call_kw/crm\.lead/web_save")):
            page.locator(".o_form_button_save").first.click()
        data = self.current(lead, "stage_id", "date_deadline")
        self.assertEqual(data["stage_id"][0], self.qualification)
        self.assertEqual(data["date_deadline"], "2026-12-18")
        page.reload(wait_until="domcontentloaded")
        self.expect_selected_stage(page, self.stage_names[1])
        self.capture(page, "02-stage-and-date-saved")
        if self.uses_won_reasons:
            page.get_by_role("button", name="Won", exact=True).click()
            dialog = page.get_by_role("dialog")
            expect(dialog.get_by_role("heading", name="Mark Won")).to_be_visible()
            dialog.get_by_text(self.won_reason_name, exact=True).click()
            self.capture(page, "03-merged-won-reasons-wizard")
            dialog.get_by_role("button", name="Mark as Won", exact=True).click()
            expect(dialog).to_be_hidden()
            self.expect_selected_stage(page, f"Won {self.run_id}")
            data = self.current(lead, "stage_id", "won_status", "won_reason_id", "date_deadline")
            self.assertEqual(data["stage_id"][0], self.won_stage)
            self.assertEqual(data["won_status"], "won")
            self.assertEqual(data["won_reason_id"][0], self.won_reason)
            self.assertEqual(data["date_deadline"], "2026-12-18")

    def test_conditions_role_and_draft_value_retention(self):
        lead = self.opportunity(self.qualification, user_id=self.rep)
        context = self.new_context(width=1440)
        self.authenticate(context, self.rep_login, self.rep_password)
        page = self.open("crm.lead", lead, context=context)
        page.get_by_role("tab", name="Extra Info", exact=True).click()
        referral = page.locator(".o_field_widget[name='referred']")
        campaign = page.locator(".o_field_widget[name='campaign_id'] input")
        expect(referral).to_be_hidden()
        campaign.fill(self.campaign_name)
        page.get_by_role("option", name=self.campaign_name, exact=True).click()
        expect(referral).to_be_visible()
        referral.locator("input").fill("Referral draft retained")
        referral.locator("input").press("Tab")
        page.get_by_text("Marketing", exact=True).click()
        self.capture(page, "04a-conditional-visibility-for-salesperson")
        self.stage(page, 2)
        expect(campaign).to_have_value(self.campaign_name)
        campaign.click()
        campaign.press("Control+a")
        campaign.press("Backspace")
        campaign.press("Tab")
        expect(referral).to_have_text("Referral draft retained")
        expect(referral.locator("input")).to_be_hidden()
        self.capture(page, "04-conditional-readonly-preserves-draft")
        with page.expect_response(re.compile(r"/web/dataset/call_kw/crm\.lead/web_save")):
            page.locator(".o_form_button_save").first.click()
        data = self.current(lead, "stage_id", "referred", "campaign_id")
        self.assertEqual(data["stage_id"][0], self.review)
        self.assertEqual(data["referred"], "Referral draft retained")
        self.assertFalse(data["campaign_id"])

    def test_rule_configuration_uses_native_controls(self):
        rule = self.call("stage.rules", "create", [
            self.rule("Configuration controls", self.intake, "date_deadline", active=False),
        ])
        self.addCleanup(self.call, "stage.rules", "unlink", [[rule]])
        page = self.open("stage.rules", rule)
        [manager_group] = self.call("res.groups", "read", [[self.manager_group], ["display_name"]])
        for name, value in (
            ("stage_ids", self.stage_names[1]),
            ("group_ids", f"Stage Rules Group {self.run_id}"),
            ("group_ids", manager_group["display_name"]),
        ):
            page.locator(f".o_field_widget[name='{name}'] input").fill(value.split("/")[-1].strip())
            page.get_by_role("option", name=value, exact=True).click()
        targets = page.locator(".o_field_widget[name='target_field_ids'] input")
        targets.fill(self.picker_label)
        page.get_by_role("option", name=re.compile("Create and edit", re.I)).click()
        dialog = page.get_by_role("dialog")
        dialog.locator(".o_model_field_selector").click()
        page.get_by_text(self.picker_label, exact=True).click()
        self.capture(page, "05a-register-existing-crm-field")
        dialog.get_by_role("button", name="Save", exact=True).click()
        expect(dialog).to_be_hidden()
        for behavior, label, field in (
            ("visibility", "Show only when the condition matches", "Campaign"),
            ("enabled", "Editable only when the condition matches", "Medium"),
            ("required", "Required when the condition matches", "Priority"),
        ):
            self.choose(page, f"e_{behavior}", label)
            condition = page.locator(f".o_field_widget[name='s_{behavior}_domain']")
            condition.get_by_role("button", name="New Rule", exact=True).click()
            condition.locator(".o_model_field_selector").click()
            page.get_by_text(field, exact=True).click()
            expect(condition.get_by_text(field, exact=True)).to_be_visible()
            if behavior == "required":
                condition.locator("select").nth(1).select_option(label="Very High")
            else:
                condition.locator("select").first.select_option(label="is set")
        self.capture(page, "05-native-stage-rule-editor")
        with page.expect_response(re.compile(r"/web/dataset/call_kw/stage\.rules/web_save")):
            page.locator(".o_form_button_save").first.click()
        fields = [
            "active", "s_visibility_domain", "s_enabled_domain", "s_required_domain",
            "stage_ids", "target_field_ids", "group_ids",
        ]
        [data] = self.call("stage.rules", "read", [[rule], fields])
        self.assertEqual(len(data["target_field_ids"]), 2)
        targets = self.call("stage.rules.field", "read", [data["target_field_ids"], ["s_field_name"]])
        self.assertEqual({field["s_field_name"] for field in targets}, {"date_deadline", self.picker_field})
        self.assertEqual(len(data["group_ids"]), 2)
        self.assertEqual(set(data["stage_ids"]), {self.intake, self.qualification})
        self.assertFalse(data["active"])
        self.assertIn("campaign_id", data["s_visibility_domain"])
        self.assertIn("medium_id", data["s_enabled_domain"])
        self.assertIn("priority", data["s_required_domain"])
        self.call("stage.rules", "write", [[rule], {"active": True}])
        lead = self.opportunity(self.intake)
        page = self.open("crm.lead", lead)
        label = page.locator("label").filter(has_text=self.picker_label)
        expect(label).to_be_hidden()
        page.get_by_role("tab", name="Extra Info", exact=True).click()
        page.locator(".o_field_widget[name='campaign_id'] input").fill(self.campaign_name)
        page.get_by_role("option", name=self.campaign_name, exact=True).click()
        expect(label).to_be_visible()

    def test_independent_conditions_use_unsaved_values_for_both_fields(self):
        lead = self.opportunity(self.conditions_stage, priority="0", referred="Referral to review")
        page = self.open("crm.lead", lead)
        page.get_by_role("tab", name="Extra Info", exact=True).click()
        referral = page.locator(".o_field_widget[name='referred']")
        notes = page.locator(f".o_field_widget[name='{self.custom_field}']")
        expect(referral).to_be_hidden()
        expect(notes).to_be_hidden()
        for field, name in (("campaign_id", self.campaign_name), ("medium_id", self.medium_name)):
            page.locator(f".o_field_widget[name='{field}'] input").fill(name)
            page.get_by_role("option", name=name, exact=True).click()
            if field == "campaign_id":
                for target in (referral, notes):
                    expect(target).to_be_visible()
                    expect(target.locator("input")).to_be_hidden()
        for target in (referral, notes):
            expect(target.locator("input")).to_be_visible()
            expect(target).not_to_have_class(re.compile("o_required_modifier"))
        page.locator(".o_field_widget[name='source_id'] input").fill(self.source_name)
        page.get_by_role("option", name=self.source_name, exact=True).click()
        for target in (referral, notes):
            expect(target).to_have_class(re.compile("o_required_modifier"))
        self.assertFalse(self.current(lead, "campaign_id", "medium_id", "source_id")["source_id"])
        self.capture(page, "08-registered-field-and-independent-conditions")

    def test_native_readonly_and_required_remain_in_force(self):
        readonly_id = self.opportunity(self.native_modifiers_stage, priority="2", campaign_id=self.campaign)
        page = self.open("crm.lead", readonly_id)
        notes = page.locator(f".o_field_widget[name='{self.custom_field}']")
        expect(notes).to_have_text("Existing note")
        expect(notes.locator("input")).to_be_hidden()
        self.capture(page, "09a-native-readonly-still-applies")
        required_id = self.opportunity(self.native_modifiers_stage, priority="3", **{self.custom_field: False})
        page = self.open("crm.lead", required_id)
        expect(page.locator(f".o_field_widget[name='{self.custom_field}']")).to_be_hidden()
        heading = page.locator(".o_form_view .oe_title [name='name'] textarea")
        heading.fill("Draft with a hidden native requirement")
        heading.press("Tab")
        page.get_by_role("button", name="Save manually").click()
        notice = page.get_by_role("alert").filter(has_text="Stage rule prevents saving")
        expect(notice).to_contain_text(self.custom_label)
        expect(heading).to_have_value("Draft with a hidden native requirement")
        self.assertNotEqual(self.current(required_id, "name")["name"], "Draft with a hidden native requirement")
        self.capture(page, "09-hidden-native-required-field-blocks-save")

    def test_conflicting_rules_keep_the_draft(self):
        lead = self.opportunity(self.conflict_stage)
        page = self.open("crm.lead", lead)
        expect(self.close_date(page)).to_be_hidden()
        heading = page.locator(".o_form_view .oe_title [name='name'] textarea")
        heading.fill("Conflict must not lose this draft")
        heading.press("Tab")
        page.get_by_role("button", name="Save manually").click()
        notice = page.get_by_role("alert").filter(has_text="Stage rule prevents saving")
        expect(notice).to_contain_text("Expected Closing")
        expect(heading).to_have_value("Conflict must not lose this draft")
        self.assertNotEqual(self.current(lead, "name")["name"], "Conflict must not lose this draft")
        self.capture(page, "07-conflicting-rules-explain-why-save-is-blocked")

    def test_unconfigured_stages_keep_native_behavior(self):
        lead = self.opportunity(self.native_stage, priority="3")
        page = self.open("crm.lead", lead)
        self.click_stage(page, self.native_names[1])
        expect(page.locator(".o_form_button_save").first).to_be_visible()
        self.assertEqual(self.current(lead, "stage_id")["stage_id"][0], self.native_stage)
        # Odoo's native Lost action automatically saves ordinary form edits.
        # Configured stage changes block this path until explicitly saved.
        with page.expect_response(re.compile(r"/web/dataset/call_kw/crm\.lead/web_save")):
            page.get_by_role("button", name="Lost", exact=True).click()
        data = self.current(lead, "stage_id", "date_deadline")
        self.assertEqual(data["stage_id"][0], self.native_next)
        self.assertFalse(data["date_deadline"])
        dialog = page.get_by_role("dialog").filter(has_text="Mark Lost")
        expect(dialog.get_by_role("heading", name="Mark Lost", exact=True)).to_be_visible()
        dialog.get_by_role("button", name="Close", exact=True).first.click()
        expect(dialog).to_be_hidden()
        page.get_by_role("tab", name="Extra Info", exact=True).click()
        expect(page.locator(".o_field_widget[name='referred'] input")).to_be_visible()
        self.capture(page, "06-unconfigured-stage-is-native")


if __name__ == "__main__":
    unittest.main()
