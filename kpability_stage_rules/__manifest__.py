{
    "name": "Stage Rules",
    "version": "20.0.1.0.0",
    "summary": "Configure field behavior by CRM opportunity stage",
    "author": "Kpability",
    "category": "Sales/CRM",
    "depends": ["crm"],
    "data": [
        "security/ir.access.csv",
        "views/stage_rules_views.xml",
        "views/crm_lead_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "kpability_stage_rules/static/src/stage_rules.js",
            "kpability_stage_rules/static/src/crm_stage_rules_form.js",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
}
