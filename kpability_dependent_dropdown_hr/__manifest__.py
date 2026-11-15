{
    "name": "Kpability Dependent Dropdowns — Sales Department",
    "summary": "Optional exact-department salesperson eligibility through public employee records",
    "version": "20.0.1.0.0",
    "category": "Sales/CRM",
    "author": "Kpability",
    "license": "LGPL-3",
    "depends": ["hr", "kpability_dependent_dropdown_crm_contacts"],
    "data": [
        "data/dropdown_adapter_data.xml",
        "views/dropdown_filter_views.xml",
        "views/salesperson_views.xml",
    ],
    "installable": True,
    "application": False,
}
