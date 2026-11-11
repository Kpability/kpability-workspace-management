{
    "name": "CRM Stage Reasons",
    "version": "20.0.1.0.0",
    "summary": "Stage-specific Won and Lost Reasons",
    "author": "Kpability",
    "category": "Sales/CRM",
    "depends": ["crm"],
    "data": [
        "security/ir.access.csv",
        "views/crm_lost_reason.xml",
        "views/crm_won_reason.xml",
        "wizard/crm_lead_lost.xml",
        "wizard/crm_lead_won.xml",
        "views/crm_lead.xml",
    ],
    "installable": True,
    "license": "LGPL-3",
}
