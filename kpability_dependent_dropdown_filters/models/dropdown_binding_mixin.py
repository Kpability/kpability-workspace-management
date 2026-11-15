from odoo import api, models


class DropdownBindingMixin(models.AbstractModel):
    _name = "dropdown.binding.mixin"
    _description = "Supported Dropdown Validation"

    def _dropdown_field_names(self):
        return ()

    def _dropdown_signature(self, child_name):
        self.ensure_one()
        definitions = self.env["dropdown.adapter"]._definitions()
        bindings = [
            definition for definition in definitions.values()
            if definition["model"] == self._name and definition["child"] == child_name
        ]
        parents = [definition.get("parent") for definition in bindings]
        return (
            self[child_name].id, self.company_id.id,
            tuple(self[parent].id if parent != "id" else self.id for parent in parents if parent),
            self.is_company if any(
                binding.get("parent") == "id" and binding.get("parent_is_company")
                for binding in bindings
            ) else None,
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            for child_name in record._dropdown_field_names():
                self.env["dropdown.filters"]._validate_selection(record, child_name)
        return records

    def write(self, vals):
        before = {
            (record.id, child): record._dropdown_signature(child)
            for record in self for child in record._dropdown_field_names()
        }
        result = super().write(vals)
        # Compare final native recomputations, not just values supplied by the caller.
        for record in self:
            for child_name in record._dropdown_field_names():
                if before[(record.id, child_name)] != record._dropdown_signature(child_name):
                    self.env["dropdown.filters"]._validate_selection(record, child_name)
        return result
