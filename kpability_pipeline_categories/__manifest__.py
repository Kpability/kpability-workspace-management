{
    "name": "Kpability Pipeline Categories",
    "version": "20.0.1.1.0",
    "summary": "Reusable, company-aware categories and stage mappings for CRM pipelines",
    "description": "Configure shared or company-specific CRM pipeline categories with reusable stages, "
    "scoped pipeline boards, native sales-team restrictions and backend consistency checks.",
    "author": "Kpability",
    "category": "Sales/CRM",
    "license": "LGPL-3",
    "depends": ["crm"],
    "data": [
        "security/ir.access.csv",
        "views/crm_pipeline_category_views.xml",
        "views/crm_stage_views.xml",
        "views/crm_lead_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
}
