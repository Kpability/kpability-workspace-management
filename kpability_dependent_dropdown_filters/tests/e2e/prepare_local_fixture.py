"""Execute through odoo-bin shell ONLY on the explicitly opted-in local fixture."""

import json
import os
import secrets
from pathlib import Path

from odoo import Command
from odoo.tools import config


def prepare(env):
    if not (
        os.environ.get("DDF_ALLOW_WRITES") == "1"
        and env.cr.dbname.startswith("kpability_ddf_")
        and config["db_host"] == "127.0.0.1"
        and config["db_port"] == 55427
    ):
        raise RuntimeError("Only the opted-in disposable localhost:55427 fixture is supported")
    output = Path("/tmp/opencode/kpability-ddf-browser")
    output.mkdir(parents=True, exist_ok=True)
    if (output / "fixture.json").exists():
        raise RuntimeError("Fixture already prepared; do not overwrite existing work")
    assert not env["dropdown.filters"].search_count([]), "Prepare a newly installed fixture"
    password = secrets.token_urlsafe(24)
    env.ref("base.user_admin").password = password
    company = env.company
    group = env.ref("sales_team.group_sale_salesman")
    users = env["res.users"].with_context(no_reset_password=True).create([
        {"name": name, "login": login, "password": password,
         "group_ids": [Command.set(group.ids)], "company_id": company.id,
         "company_ids": [Command.set(company.ids)]}
        for name, login in (
            ("DDF Eligible Salesperson", "ddf_browser_sales"),
            ("DDF Other Department", "ddf_browser_other"),
        )
    ])
    department, other_department = env["hr.department"].create([
        {"name": "DDF Configured Commercial", "company_id": company.id},
        {"name": "Sales", "company_id": company.id},
    ])
    env["hr.employee"].create([
        {"name": user.name, "user_id": user.id, "company_id": company.id, "department_id": dept.id}
        for user, dept in zip(users, (department, other_department))
    ])
    customer_a, customer_b = env["res.partner"].create([
        {"name": "DDF Browser Company A", "vat": "US123456789", "company_id": company.id},
        {"name": "DDF Browser Company B", "vat": "US987654321", "company_id": company.id},
    ])
    people_a = env["res.partner"].create([
        {"name": f"DDF Browser A Person {index:02}", "parent_id": customer_a.id,
         "company_id": company.id}
        for index in range(1, 13)
    ])
    person_b = env["res.partner"].create({
        "name": "DDF Browser B Person", "parent_id": customer_b.id, "company_id": company.id,
    })
    env["res.partner"].create({
        "name": "DDF Browser Archived", "parent_id": customer_a.id,
        "company_id": company.id, "active": False,
    })
    leads = env["crm.lead"].create([
        {"name": f"DDF Browser {kind.title()}", "type": kind, "company_id": company.id,
         "user_id": users[0].id, "customer_company_id": customer_a.id,
         "partner_id": people_a[0].id}
        for kind in ("opportunity", "lead")
    ])
    rules = env["dropdown.filters"].create([
        {"s_name": f"DDF Browser {adapter.s_name}", "company_id": company.id,
         "adapter_id": adapter.id, "active": True,
         "department_id": department.id if "sales_department" in adapter.s_key else False}
        for adapter in env["dropdown.adapter"].search([])
    ])
    customer_a.primary_contact_id = people_a[0]
    env.flush_all()
    fixture = {
        "database": env.cr.dbname, "company": company.id, "users": users.ids,
        "customer_a": customer_a.id, "customer_b": customer_b.id,
        "people_a": people_a.ids, "person_b": person_b.id,
        "opportunity": leads[0].id, "lead": leads[1].id, "rules": rules.ids,
    }
    credentials = output / "credentials.json"
    credentials.write_text(json.dumps({"admin": password, "sales": password}))
    credentials.chmod(0o600)
    (output / "fixture.json").write_text(json.dumps(fixture, indent=2) + "\n")
    env.cr.commit()


if "env" in globals():
    prepare(env)
