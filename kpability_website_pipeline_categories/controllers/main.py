from odoo import _
from odoo.exceptions import UserError
from odoo.addons.website_crm.controllers.website_form import WebsiteForm


class RetiredWebsitePipelineForm(WebsiteForm):
    """Reject stale pipeline submissions; leave ordinary native forms alone."""

    def _handle_website_form(self, model_name, **kwargs):
        if model_name == "crm.lead" and any(
            key == "kp_pipeline_category_ids" or key.startswith("kp_pipeline_category_id_")
            for key in kwargs
        ):
            raise UserError(_("Website pipeline intake is unavailable. Please contact us directly."))
        return super()._handle_website_form(model_name, **kwargs)
