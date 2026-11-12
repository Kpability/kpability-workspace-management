{
    "name": "Menu Management",
    "version": "20.0.1.0.0",
    "author": "Kpability",
    "license": "LGPL-3",
    "depends": ["workspace_management"],
    "data": [
        "security/ir.access.csv",
        "views/menu_management.xml",
    ],
    "assets": {
        "web.assets_backend": ["menu_management/static/src/**/*"],
    },
    "installable": True,
}
