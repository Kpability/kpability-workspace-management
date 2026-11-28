{
    "name": "Kpability Sales Team Pipeline Categories",
    "summary": "Explicit sales-team eligibility for CRM pipeline categories",
    "version": "20.0.1.0.0",
    "category": "Sales/CRM",
    "author": "Kpability",
    "license": "LGPL-3",
    "depends": ["kpability_pipeline_categories"],
    "data": [
        "views/crm_team_views.xml",
        "views/crm_pipeline_category_views.xml",
        "views/crm_lead_views.xml",
        "views/pipeline_team_compatibility_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "kpability_sales_team_pipeline_categories/static/src/views/compatibility_views.js",
        ],
    },
    "installable": True,
    "application": False,
}
