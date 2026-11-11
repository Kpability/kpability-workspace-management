{
    "name": "Workspace Management",
    "version": "20.0.1.0.0",
    "summary": "Central workspace administration",
    "author": "Kpability",
    "category": "Administration",
    "depends": ["base", "web"],
    "data": [
        "data/system_parameters.xml",
        "views/res_users.xml",
        "views/workspace_menu.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "workspace_management/static/src/user_roles/user_roles.js",
            "workspace_management/static/src/user_roles/user_roles.xml",
            "workspace_management/static/src/user_roles/user_roles.scss",
        ],
    },
    "application": True,
    "installable": True,
    "license": "LGPL-3",
}