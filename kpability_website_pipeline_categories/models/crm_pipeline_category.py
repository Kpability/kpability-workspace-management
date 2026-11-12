from odoo import api, fields, models


class CrmPipelineCategory(models.Model):
    _inherit = "crm.pipeline.category"

    website_ids = fields.Many2many(
        "website",
        "crm_pipeline_category_website_rel",
        "category_id",
        "website_id",
        string="Websites",
        help="Websites where visitors can select this pipeline in a CRM form.",
    )

    @api.model
    def _get_website_categories(self, website):
        if not website:
            return self.browse()
        company = website.company_id
        domain = [
            ("active", "=", True),
            ("website_ids", "in", website.ids),
            ("stage_ids", "!=", False),
        ]
        if company:
            domain += [
                "|",
                ("company_id", "=", False),
                ("company_id", "=", company.id),
            ]
        else:
            domain += [("company_id", "=", False)]
        return self.sudo().search(domain, order="n_sequence, s_name, id")

    def _is_available_on_website(self, website):
        self.ensure_one()
        if not self.active or not self.stage_ids or website not in self.website_ids:
            return False
        return not self.company_id or self.company_id == website.company_id
