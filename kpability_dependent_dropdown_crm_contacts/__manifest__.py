{
    "name": "Kpability Dependent Dropdowns — CRM and Contacts",
    "summary": "Configured customer-company/contact selectors using native Odoo domains",
    "version": "20.0.1.0.0",
    "category": "Sales/CRM",
    "author": "Kpability",
    "license": "LGPL-3",
    "depends": ["crm", "contacts", "kpability_dependent_dropdown_filters"],
    "data": [
        "data/dropdown_adapter_data.xml",
        "views/crm_lead_views.xml",
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
}
