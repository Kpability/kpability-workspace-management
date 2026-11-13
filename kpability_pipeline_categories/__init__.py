from . import models


def post_init_hook(env):
    """Create the starter pipeline only on installation, without replacing data."""
    Category = env["crm.pipeline.category"].with_context(active_test=False)
    if Category.search_count([("s_name", "=", "General Sales"), ("company_id", "=", False)]):
        return
    stages = (
        env.ref("crm.stage_lead1")
        | env.ref("crm.stage_lead2")
        | env.ref("crm.stage_lead3")
        | env.ref("crm.stage_lead4")
    )
    Category.create({
        "s_name": "General Sales",
        "s_description": "Standard sales opportunities using the default CRM stages.",
        "n_sequence": 10,
        "company_id": False,
        "stage_ids": [(6, 0, stages.ids)],
    })
