from odoo import _, http
from odoo.exceptions import UserError
from odoo.http import request
from odoo.addons.website_crm.controllers.website_form import WebsiteForm


class WebsitePipelineCategoryForm(WebsiteForm):

    def _handle_website_form(self, model_name, **kwargs):
        request.kp_pipeline_category_ids = []
        request.kp_pipeline_created_record_ids = []
        if model_name == "crm.lead":
            prefix = "kp_pipeline_category_id_"
            for parameter in list(kwargs):
                if not parameter.startswith(prefix):
                    continue
                value = kwargs.pop(parameter)
                try:
                    request.kp_pipeline_category_ids.append(int(value))
                except (TypeError, ValueError):
                    raise UserError(_("One of the selected pipelines is invalid. Refresh the page and try again."))
            comma_separated = kwargs.pop("kp_pipeline_category_ids", "")
            if comma_separated:
                try:
                    request.kp_pipeline_category_ids.extend(
                        int(value) for value in comma_separated.split(",") if value.strip()
                    )
                except ValueError:
                    raise UserError(_("One of the selected pipelines is invalid. Refresh the page and try again."))
        return super()._handle_website_form(model_name, **kwargs)

    def insert_record(self, request, model_sudo, values, custom, meta=None):
        category_ids = list(dict.fromkeys(getattr(request, "kp_pipeline_category_ids", [])))
        if model_sudo.model != "crm.lead" or not category_ids:
            return super().insert_record(request, model_sudo, values, custom, meta=meta)

        website = request.env.website
        categories = request.env["crm.pipeline.category"].sudo().browse(category_ids).exists()
        categories = categories.filtered(lambda category: category._is_available_on_website(website))
        if len(categories) != len(category_ids):
            raise UserError(_(
                "One of the selected pipelines is no longer available on this website. "
                "Refresh the page and choose again."
            ))

        first_record_id = False
        for category in categories.sorted("n_sequence"):
            category_values = dict(values, pipeline_category_id=category.id)
            record_id = super().insert_record(
                request, model_sudo, category_values, custom, meta=meta,
            )
            request.kp_pipeline_created_record_ids.append(record_id)
            first_record_id = first_record_id or record_id
        return first_record_id

    def insert_attachment(self, model_sudo, id_record, files):
        record_ids = getattr(request, "kp_pipeline_created_record_ids", [])
        if model_sudo.model == "crm.lead" and len(record_ids) > 1 and id_record in record_ids:
            for pipeline_record_id in record_ids:
                for upload in files:
                    upload.seek(0)
                super().insert_attachment(model_sudo, pipeline_record_id, files)
            return
        return super().insert_attachment(model_sudo, id_record, files)


class WebsitePipelineCategoryController(http.Controller):

    @http.route(
        "/kpability/pipeline-categories",
        type="http",
        auth="public",
        website=True,
        methods=["GET"],
        csrf=False,
    )
    def website_pipeline_categories(self, **kwargs):
        categories = request.env["crm.pipeline.category"].sudo()._get_website_categories(request.env.website)
        return request.make_json_response([
            {
                "id": category.id,
                "name": category.s_name,
                "description": category.s_description or "",
            }
            for category in categories
        ])
