from odoo import api, fields, models
from odoo.exceptions import ValidationError


class DropdownAdapter(models.Model):
    _name = "dropdown.adapter"
    _description = "Supported Dropdown Binding"
    _rec_name = "s_name"
    _order = "s_name, id"

    s_name = fields.Char(string="Binding", required=True, translate=True)
    s_key = fields.Char(string="Technical Key", required=True, index=True)

    _key_unique = models.Constraint("UNIQUE(s_key)", "A binding key must be unique.")

    @api.model
    def _definitions(self):
        """Adapters extend this code allow-list; configuration never executes code."""
        return {}

    @api.constrains("s_key")
    def _check_definition(self):
        definitions = self._definitions()
        for adapter in self:
            definition = definitions.get(adapter.s_key)
            if not definition:
                raise ValidationError(self.env._("This dropdown binding is not supported."))
            model = self.env[definition["model"]]
            child = model._fields.get(definition["child"])
            if not child or child.type != "many2one":
                raise ValidationError(self.env._("The binding requires a supported Many2one field."))
            if definition.get("parent"):
                parent = definition["parent"]
                if parent != "id" and (
                    parent not in model._fields or model._fields[parent].type != "many2one"
                ):
                    raise ValidationError(self.env._("The parent field is not supported."))
                inverse = self.env[child.comodel_name]._fields.get(definition["inverse"])
                parent_model = model._name if parent == "id" else model._fields[parent].comodel_name
                if not inverse or inverse.type != "many2one" or inverse.comodel_name != parent_model:
                    raise ValidationError(self.env._("The binding has incompatible relation fields."))
                # No target can also be a parent of another binding on this model.
                for other in definitions.values():
                    if other["model"] == model._name and (
                        other.get("parent") == definition["child"]
                        or other["child"] == definition.get("parent")
                    ):
                        raise ValidationError(self.env._("Chained dropdown bindings are not supported."))
