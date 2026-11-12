{
    "name": "Kpability Website Pipeline Categories",
    "version": "20.0.1.0.0",
    "summary": "Let website visitors create CRM opportunities in one or more pipelines",
    "description": "Publish a CRM form that lists the pipeline categories enabled for the current website. "
    "One submission creates one opportunity per selected pipeline, preserving native website CRM behavior.",
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
