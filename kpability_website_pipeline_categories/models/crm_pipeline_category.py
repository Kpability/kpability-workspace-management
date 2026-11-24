from odoo import fields, models


class CrmPipelineCategory(models.Model):
    _inherit = "crm.pipeline.category"

    # Storage compatibility only: do not drop existing mappings on upgrade.
    website_ids = fields.Many2many(
        "website",
        "crm_pipeline_category_website_rel",
        "category_id",
        "website_id",
        string="Retired Websites",
        readonly=True,
        help="Historical configuration retained for the deferred website integration.",
    )
