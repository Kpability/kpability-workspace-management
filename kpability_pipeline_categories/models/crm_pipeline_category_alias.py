import ast

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class CrmPipelineCategoryAlias(models.Model):
    _name = "crm.pipeline.category.alias"
    _description = "Pipeline Category Incoming Email Address"
    _order = "category_id, alias_name, id"

    category_id = fields.Many2one(
        "crm.pipeline.category",
        required=True,
        ondelete="cascade",
        index=True,
    )
    alias_id = fields.Many2one(
        "mail.alias",
        required=True,
        ondelete="cascade",
        readonly=True,
        copy=False,
        index=True,
    )
    alias_name = fields.Char(required=True)
    alias_domain_id = fields.Many2one(
        "mail.alias.domain",
        string="Domain",
        required=True,
        default=lambda self: self.env.company.alias_domain_id,
    )
    alias_full_name = fields.Char(compute="_compute_alias_full_name", store=True)
    company_id = fields.Many2one(related="category_id.company_id", store=True, index=True)

    _alias_name_domain_unique = models.UniqueIndex(
        "(alias_name, COALESCE(alias_domain_id, 0))",
        "This incoming email address is already used by another pipeline.",
    )

    @api.depends("alias_name", "alias_domain_id")
    def _compute_alias_full_name(self):
        for record in self:
            record.alias_full_name = (
                f"{record.alias_name}@{record.alias_domain_id.name}"
                if record.alias_name and record.alias_domain_id
                else record.alias_name
            )

    @api.constrains("alias_name")
    def _check_alias_name(self):
        for record in self:
            self._validate_alias_name(record.alias_name)

    @api.model
    def _validate_alias_name(self, alias_name):
        if not (alias_name or "").strip():
            raise ValidationError(_("Enter an incoming email address without its domain."))
        if "@" in alias_name:
            raise ValidationError(_("Enter only the part before @. Choose the domain in the Domain field."))

    def _prepare_mail_alias_values(self, vals):
        defaults = {
            "pipeline_category_id": vals["category_id"],
            "type": "opportunity",
        }
        return {
            "alias_name": vals["alias_name"],
            "alias_domain_id": vals.get("alias_domain_id") or self.env.company.alias_domain_id.id,
            "alias_model_id": self.env["ir.model"]._get_id("crm.lead"),
            "alias_parent_model_id": self.env["ir.model"]._get_id("crm.pipeline.category"),
            "alias_parent_thread_id": vals["category_id"],
            "alias_defaults": repr(defaults),
            "alias_contact": "everyone",
        }

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access("create")
        prepared = []
        for vals in vals_list:
            vals = dict(vals)
            self._validate_alias_name(vals.get("alias_name"))
            vals["alias_id"] = self.env["mail.alias"].sudo().create(
                self._prepare_mail_alias_values(vals)
            ).id
            prepared.append(vals)
        return super().create(prepared)

    def write(self, vals):
        self.check_access("write")
        alias_vals = {}
        for field_name in ("alias_name", "alias_domain_id"):
            if field_name in vals:
                alias_vals[field_name] = vals[field_name]
        if alias_vals or "category_id" in vals:
            for record in self:
                values = dict(alias_vals)
                if "category_id" in vals:
                    values["alias_defaults"] = repr({
                        "pipeline_category_id": vals["category_id"],
                        "type": "opportunity",
                    })
                    values["alias_parent_thread_id"] = vals["category_id"]
                record.alias_id.sudo().write(values)
        return super().write(vals)

    def unlink(self):
        self.check_access("unlink")
        aliases = self.alias_id
        result = super().unlink()
        aliases.sudo().unlink()
        return result

    def _get_route_category_id(self):
        """Return the category carried by this alias' native mail defaults."""
        self.ensure_one()
        try:
            defaults = ast.literal_eval(self.alias_id.alias_defaults or "{}")
        except (SyntaxError, ValueError):
            return False
        return defaults.get("pipeline_category_id") if isinstance(defaults, dict) else False
