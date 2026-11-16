{
    "name": "Kpability Website Pipeline Categories (Retired)",
    "version": "20.0.1.1.0",
    "summary": "Upgrade compatibility only; website pipeline intake is deferred",
    "description": "Retain existing website mappings and safely retire the website pipeline form. "
    "This compatibility module does not offer pipeline intake. Follow-up work is tracked in issue #6.",
    "author": "Kpability",
    "category": "Website/Website",
    "license": "LGPL-3",
    "depends": [
        "kpability_pipeline_categories",
        "website_crm",
    ],
    "data": [
        "views/crm_pipeline_category_views.xml",
        "views/website_templates.xml",
        "views/snippets.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "kpability_website_pipeline_categories/static/src/js/pipeline_category_form.js",
        ],
    },
    "installable": True,
    "application": False,
}
