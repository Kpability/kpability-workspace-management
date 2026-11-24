from odoo import api, models


class MailThread(models.AbstractModel):
    _inherit = "mail.thread"

    @api.model
    def message_route(self, message, message_dict, model=None, thread_id=None, custom_values=None):
        routes = super().message_route(
            message, message_dict, model=model, thread_id=thread_id, custom_values=custom_values,
        )
        return self._deduplicate_pipeline_category_routes(routes)

    def _deduplicate_pipeline_category_routes(self, routes):
        """Create one CRM record per pipeline for one incoming message.

        Native routing creates one record per matching alias. Two addresses can
        deliberately point to the same pipeline, but a single email addressed to
        both must not create duplicate opportunities in that pipeline.
        """
        deduplicated = []
        seen_categories = set()
        for route in routes or ():
            route_model, route_thread_id, route_values, _user_id, _alias = route
            if route_model == "crm.lead" and not route_thread_id and isinstance(route_values, dict):
                category_id = route_values.get("pipeline_category_id")
                if category_id:
                    if category_id in seen_categories:
                        continue
                    seen_categories.add(category_id)
            deduplicated.append(route)
        return deduplicated
