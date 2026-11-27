{
    "name": "CRM Stage Templates",
    "version": "20.0.1.0.0",
    "summary": "Centralized stage-specific activity, email, and stage-rule templates",
    "author": "Kpability",
    "category": "Sales/CRM",
    "depends": ["crm", "mail"],
    "data": [
        "security/ir.access.csv",
        "views/crm_stage_template.xml",
        "views/crm_stage_templates_menu.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
