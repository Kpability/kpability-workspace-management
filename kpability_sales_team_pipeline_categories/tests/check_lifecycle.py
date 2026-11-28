"""Execute with odoo-bin shell, not through the Odoo test loader.

ODOO_STPC_LIFECYCLE_MODE=seed|after_install|after_update
ODOO_STPC_LIFECYCLE_SNAPSHOT=/tmp/opencode/<unique-run>.json
Requires an explicit disposable database opt-in. Leaves synthetic fixtures for
inspection. Never uses SQL, modifies existing business fixtures or infers maps.
"""

import json
import os
from pathlib import Path

from odoo import Command


def normalized(value):
    return json.loads(json.dumps(value, default=str))


def snapshot(environment, identifiers):
    return normalized({
        "leads": environment["crm.lead"].with_context(active_test=False).browse(identifiers["leads"]).read([
            "name", "type", "team_id", "company_id", "pipeline_category_id", "stage_id",
            "active", "probability", "expected_revenue", "create_date", "write_date",
        ]),
        "stages": environment["crm.stage"].browse(identifiers["stages"]).read([
            "name", "sequence", "team_ids", "is_won", "fold", "create_date", "write_date",
        ]),
        "categories": environment["crm.pipeline.category"].with_context(active_test=False).browse(
            identifiers["categories"],
        ).read(["s_name", "active", "company_id", "stage_ids", "create_date", "write_date"]),
    })


def run(environment):
    assert os.environ.get("ODOO_E2E_ALLOW_WRITES") == "1", "Explicit disposable-database opt-in required"
    assert environment.cr.dbname.startswith("kpability_pipeline_stpc_"), "Use a dedicated STPC test database"
    path = Path(os.environ["ODOO_STPC_LIFECYCLE_SNAPSHOT"]).resolve()
    assert path.is_relative_to(Path("/tmp/opencode")), "Keep synthetic snapshots outside the repository"
    mode = os.environ["ODOO_STPC_LIFECYCLE_MODE"]
    Lead, Team, Category = (environment[name] for name in ("crm.lead", "crm.team", "crm.pipeline.category"))
    if mode == "seed":
        assert not path.exists(), "Do not overwrite an existing lifecycle baseline"
        assert "pipeline_category_ids" not in Team._fields, "Seed before installing the consumer"
        team = Team.create({"name": "STPC Lifecycle Existing Team", "company_id": environment.company.id})
        stages = environment["crm.stage"].create([
            {"name": "STPC Lifecycle Intake", "sequence": -7000},
            {"name": "STPC Lifecycle Won", "sequence": 7000, "is_won": True},
        ])
        category = Category.create({
            "s_name": "STPC Lifecycle Existing Category", "company_id": environment.company.id,
            "stage_ids": [Command.set(stages.ids)],
        })
        values = {"type": "opportunity", "team_id": team.id, "company_id": environment.company.id,
                  "user_id": False, "pipeline_category_id": category.id, "expected_revenue": 100}
        leads = Lead.create([{**values, "name": f"STPC Lifecycle {state}"} for state in ("Open", "Won", "Lost")])
        leads[1].action_set_won()
        leads[2].action_set_lost()
        leads |= Lead.create({**values, "name": "STPC Lifecycle Native", "pipeline_category_id": False})
        identifiers = {"leads": leads.ids, "stages": stages.ids, "categories": category.ids, "team": team.id}
        baseline = {"database": environment.cr.dbname, "ids": identifiers, "before": snapshot(environment, identifiers)}
        path.write_text(json.dumps(baseline, indent=2))
        environment.cr.commit()
        print("STPC lifecycle: seeded pre-install categorized Open/Won/Lost and unclassified CRM records")
        return

    assert mode in {"after_install", "after_update"}, "Unsupported lifecycle mode"
    baseline = json.loads(path.read_text())
    assert baseline["database"] == environment.cr.dbname, "Snapshot belongs to a different database"
    identifiers = baseline["ids"]
    assert snapshot(environment, identifiers) == baseline["before"], "CRM/configuration or audit history changed"
    team = Team.browse(identifiers["team"])
    if mode == "after_install":
        assert not Team.with_context(active_test=False).search([]).pipeline_category_ids, "Installation inferred mappings"
        admin = environment.ref("base.user_admin")
        action = Lead.with_user(admin).action_open_pipeline_team_compatibility()
        mismatches = Lead.with_user(admin).with_context(active_test=False).search(action["domain"])
        assert set(identifiers["leads"][:3]).issubset(mismatches.ids), "Report missed historical mismatches"
        assert identifiers["leads"][3] not in mismatches.ids, "Unclassified CRM should not be reclassified"
        assert snapshot(environment, identifiers) == baseline["before"], "Report mutated records"
        # This is the explicit rollout decision, not an inferred migration.
        team.write({"pipeline_category_ids": [Command.set(identifiers["categories"])]})
        assert snapshot(environment, identifiers) == baseline["before"], "Explicit mapping rewrote CRM history"
    else:
        assert team.pipeline_category_ids.ids == identifiers["categories"], "Update changed explicit mappings"
    environment.cr.commit()
    print(f"STPC lifecycle: {mode} preserved records, stages, categories and audit dates")


run(env)  # noqa: F821 - supplied explicitly by odoo-bin shell
