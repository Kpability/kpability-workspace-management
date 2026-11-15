import ast

from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain


class DropdownFilters(models.Model):
    _name = "dropdown.filters"
    _description = "Dependent Dropdown Filter"
    _rec_name = "s_name"
    _order = "company_id, adapter_id, id"
    _check_company_auto = True

    s_name = fields.Char(string="Name", required=True)
    active = fields.Boolean(default=False)
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company, index=True,
    )
    adapter_id = fields.Many2one(
        "dropdown.adapter", string="Supported Binding", required=True, ondelete="restrict",
    )

    _binding_company_unique = models.Constraint(
        "UNIQUE(company_id, adapter_id)",
        "Use one maintained filter per company and binding, including archived filters.",
    )

    @api.constrains("adapter_id", "company_id", "active")
    def _check_configuration(self):
        self.adapter_id._check_definition()

    @api.model
    def _get_rule(self, record, child_name):
        record.ensure_one()
        company = record.company_id or record.env.company
        keys = [
            key for key, definition in self.env["dropdown.adapter"]._definitions().items()
            if definition["model"] == record._name and definition["child"] == child_name
        ]
        return self.with_context(active_test=False).search([
            ("active", "=", True),
            ("company_id", "=", company.id), ("adapter_id.s_key", "in", keys),
        ], limit=1) if keys else self.browse()

    @api.model
    def _native_domain(self, record, child_name):
        """Keep the installed Python domain and Odoo's company-consistency domain."""
        field = record._fields[child_name]
        native = field.domain(record) if callable(field.domain) else field.domain
        # Unsupported future expression domains must not silently become unrestricted.
        if isinstance(native, str):
            try:
                native = ast.literal_eval(native)
            except (ValueError, SyntaxError) as error:
                raise ValidationError(record.env._(
                    "This selector now uses an unsupported expression domain. "
                    "Ask an administrator to review its dropdown adapter."
                )) from error
        domain = Domain(native or [])
        if field.check_company:
            domain &= Domain(record.env[field.comodel_name]._check_company_domain(record.company_id))
        return domain

    def _domain_for_rule(self, record):
        self.ensure_one()
        definition = self.env["dropdown.adapter"]._definitions()[self.adapter_id.s_key]
        parent = record if definition["parent"] == "id" else record[definition["parent"]]
        parent_id = parent._origin.id or parent.id
        if not parent or not isinstance(parent_id, int):
            return Domain.FALSE
        try:
            saved_parent = parent.browse(parent_id)
            saved_parent.check_access("read")
            if definition.get("parent_is_company") and not parent.is_company:
                return Domain.FALSE
            if not saved_parent.exists() or not saved_parent.search(
                Domain("id", "=", parent_id) & Domain(definition.get("parent_domain", [])),
                limit=1,
            ):
                return Domain.FALSE
        except AccessError:
            return Domain.FALSE
        return Domain.AND([
            [(definition["inverse"], "=", parent_id)],
            definition.get("candidate_domain", []),
        ])

    @api.model
    def _get_domain(self, record, child_name, native_domain=()):
        native = self._native_domain(record, child_name) & Domain(native_domain)
        rule = self._get_rule(record, child_name)
        return native & rule._domain_for_rule(record) if rule else native

    @api.model
    def _get_state(self, record, child_name):
        domain = self._get_domain(record, child_name)
        rule = self._get_rule(record, child_name)
        hint = False
        if rule:
            definition = self.env["dropdown.adapter"]._definitions()[rule.adapter_id.s_key]
            child = record[child_name]
            target = self.env[record._fields[child_name].comodel_name]
            if child and not target.search(domain & Domain("id", "=", child.id), limit=1):
                hint = self.env._(
                    "The selection no longer matches this filter. Clear it or select an eligible "
                    "record before changing this relationship. Unrelated legacy edits are allowed."
                )
            elif definition.get("parent"):
                parent = record if definition["parent"] == "id" else record[definition["parent"]]
                if not parent or not isinstance(parent._origin.id or parent.id, int):
                    hint = self.env._(
                        "Select a saved customer company first. No contact choices are available yet."
                    )
            if not hint and not target.search(domain, limit=1):
                hint = self.env._(
                    "No eligible records are available. Check the company, filter configuration "
                    "and your access with an administrator."
                )
        return list(domain), hint

    @api.model
    def _validate_selection(self, record, child_name):
        if not record[child_name] or not self._get_rule(record, child_name):
            return
        target = self.env[record._fields[child_name].comodel_name]
        domain = self._get_domain(record, child_name) & Domain("id", "=", record[child_name].id)
        if not target.search(domain, limit=1):
            raise ValidationError(self.env._(
                "The selected record does not match the active dropdown filter. "
                "Clear it or select an eligible record before saving."
            ))
