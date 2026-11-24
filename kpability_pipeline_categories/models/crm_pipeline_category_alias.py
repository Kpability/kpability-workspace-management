from odoo import _, api, fields, models
from odoo.exceptions import AccessError, UserError


class CrmPipelineCategoryAlias(models.Model):
    """Read-only upgrade archive, not an incoming-email integration.

    Retaining the model prevents Odoo from removing existing configuration when
    upgrading databases that installed the email feature from PR #4.
    """

    _name = "crm.pipeline.category.alias"
    _description = "Retired Pipeline Category Email Configuration"
    _order = "category_id, alias_name, id"

    category_id = fields.Many2one(
        "crm.pipeline.category", required=True, ondelete="cascade", index=True, readonly=True,
    )
    alias_id = fields.Many2one(
        "mail.alias", required=True, ondelete="cascade", readonly=True, copy=False, index=True,
    )
    alias_name = fields.Char(required=True, readonly=True)
    alias_domain_id = fields.Many2one("mail.alias.domain", string="Domain", required=True, readonly=True)
    alias_full_name = fields.Char(compute="_compute_alias_full_name", store=True)
    company_id = fields.Many2one(related="category_id.company_id", store=True, index=True)
    s_deferred_alias_name = fields.Char(readonly=True, copy=False)

    _alias_name_domain_unique = models.UniqueIndex(
        "(alias_name, COALESCE(alias_domain_id, 0))",
        "This retired incoming email address is already recorded for another pipeline.",
    )

    @api.depends("alias_name", "alias_domain_id")
    def _compute_alias_full_name(self):
        for record in self:
            record.alias_full_name = (
                f"{record.alias_name}@{record.alias_domain_id.name}"
                if record.alias_name and record.alias_domain_id else record.alias_name
            )

    @api.model_create_multi
    def create(self, vals_list):
        self.check_access("create")
        raise UserError(_("Pipeline email intake is deferred. Existing configuration is read-only."))

    def write(self, vals):
        self.check_access("write")
        raise UserError(_("Pipeline email intake is deferred. Existing configuration is read-only."))

    def unlink(self):
        self.check_access("unlink")
        raise UserError(_("Retired pipeline email configuration is retained for a future migration."))

    def _defer_intake(self):
        """Upgrade-only: retain exact alias names and disable only owned aliases."""
        if not self.env.su:
            raise AccessError(_("Only the upgrade process may retire pipeline email aliases."))
        for record in self:
            if record.alias_id.alias_name:
                if not record.s_deferred_alias_name:
                    super(CrmPipelineCategoryAlias, record).write({
                        "s_deferred_alias_name": record.alias_id.alias_name,
                    })
                record.alias_id.write({"alias_name": False})
