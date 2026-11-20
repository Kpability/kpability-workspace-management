{
    "name": "CRM Keyword Assignment",
    "version": "20.0.1.1.0",
    "summary": "Assign salespersons to leads using field keyword rules",
    "author": "Kpability",
    "category": "Sales/CRM",
    "depends": ["crm"],
    "data": [
        "security/ir.access.csv",
        "views/crm_keyword_assignment.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "crm_keyword_assignment/static/src/list_controller.js",
        ],
    },
    "installable": True,
    "license": "LGPL-3",
}
