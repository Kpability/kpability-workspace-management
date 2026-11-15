"""Run through odoo-bin shell before installation, after installation and upgrade."""

import json
import os
from pathlib import Path

from odoo.tools import config


def check(env):
    if not (os.environ.get("DDF_ALLOW_WRITES") == "1"
            and env.cr.dbname == "kpability_ddf_legacy"
            and config["db_host"] == "127.0.0.1" and config["db_port"] == 55427):
        raise RuntimeError("Only the explicitly opted-in disposable legacy fixture is supported")
    path = Path("/tmp/opencode/kpability-ddf-lifecycle.json")
    phase = os.environ["DDF_LIFECYCLE_PHASE"]
    fields = {
        "res.partner": ["name", "active", "parent_id", "company_id", "user_id", "vat",
                        "create_date", "write_date", "create_uid", "write_uid"],
        "crm.lead": ["name", "active", "partner_id", "partner_name", "company_id", "user_id",
                     "team_id", "stage_id", "create_date", "write_date", "create_uid", "write_uid"],
    }
    if phase == "before":
        if path.exists():
            raise RuntimeError("Existing snapshot must not be overwritten")
        assert "dropdown.filters" not in env
        parent = env["res.partner"].create({
            "name": "DDF Legacy Company", "vat": "US123456789", "company_id": env.company.id,
        })
        child = env["res.partner"].create({
            "name": "DDF Legacy Individual", "parent_id": parent.id, "company_id": env.company.id,
        })
        lead = env["crm.lead"].create({
            "name": "DDF Existing Opportunity", "type": "opportunity",
            "partner_id": child.id, "company_id": env.company.id,
        })
        env.flush_all()
        snapshot = {
            "database": env.cr.dbname,
            "ids": {"res.partner": (parent | child).ids, "crm.lead": lead.ids},
            "checks": [],
        }
    else:
        assert phase in {"after_install", "after_upgrade"}
        snapshot = json.loads(path.read_text())
        assert not env["dropdown.filters"].with_context(active_test=False).search_count([])
        assert env["dropdown.adapter"].search_count([]) == 4
        assert not env["res.partner"].browse(snapshot["ids"]["res.partner"]).mapped("primary_contact_id")
        assert not env["crm.lead"].browse(snapshot["ids"]["crm.lead"]).mapped("customer_company_id")
    current = {
        model: env[model].browse(ids).read(fields[model])
        for model, ids in snapshot["ids"].items()
    }
    # Normalize datetimes exactly as the persisted JSON snapshot.
    current = json.loads(json.dumps(current, default=str))
    if phase == "before":
        snapshot["before"] = current
    else:
        assert current == snapshot["before"], "Installation/upgrade changed existing fixture records"
    snapshot["checks"].append({"phase": phase, "preserved": True})
    path.write_text(json.dumps(snapshot, indent=2) + "\n")
    env.cr.commit()
    print(f"Lifecycle check passed: {phase}; snapshot {path}")


if "env" in globals():
    check(env)
