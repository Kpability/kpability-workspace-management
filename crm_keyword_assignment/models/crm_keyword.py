from odoo import fields, models


class CrmKeyword(models.Model):
    _name = "crm.keyword"
    _description = "CRM Keyword"
    _order = "s_name, id"
    _rec_name = "s_name"

    s_name = fields.Char("Keyword", required=True, index=True)
