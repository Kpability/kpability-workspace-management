import unicodedata
from ast import literal_eval

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
from odoo.fields import Domain


class CrmPipelineCategory(models.Model):
    _name = "crm.pipeline.category"
    _description = "CRM Pipeline Category"
    _rec_name = "s_name"
    _order = "n_sequence, s_name, id"

    s_name = fields.Char(string="Name", required=True, translate=True)
    s_description = fields.Text(string="Description", translate=True)
    n_sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        index=True,
        help="Leave empty to share this category across companies. This does not grant access to opportunities.",
    )
    stage_ids = fields.Many2many(
        "crm.stage",
        "crm_pipeline_category_stage_rel",
        "category_id",
        "stage_id",
        string="Stages",
        help="Only these stages can be used by categorized records. Native sales-team restrictions still apply.",
    )
    s_normalized_name = fields.Char(compute="_compute_normalized_name", store=True, precompute=True)
    lead_count = fields.Integer(compute="_compute_lead_count")

    _name_scope_unique = models.Constraint(
        "UNIQUE NULLS NOT DISTINCT (company_id, s_normalized_name)",
        "A pipeline category with this name already exists in this company or shared scope, including archived categories.",
    )

    @api.depends("s_name")
    def _compute_normalized_name(self):
        for category in self.with_context(lang=None):
            name = unicodedata.normalize("NFKC", category.s_name or "")
            category.s_normalized_name = " ".join(name.split()).casefold()

    @api.constrains("s_name")
    def _check_name(self):
        for category in self:
            if not (category.s_name or "").strip():
                raise ValidationError(_("Enter a non-empty pipeline category name."))

    @api.depends("stage_ids")
    def _compute_lead_count(self):
        counts = dict(self.env["crm.lead"]._read_group(
            [("pipeline_category_id", "in", self.ids), ("type", "=", "opportunity")],
            ["pipeline_category_id"],
            ["__count"],
        ))
        for category in self:
            category.lead_count = counts.get(category, 0)

    def _check_assignable(self):
        """Shared assignment contract for CRM and optional category consumers."""
        self.check_access("read")
        if any(not category.active for category in self):
            raise ValidationError(_("Archived pipeline categories cannot be assigned. Choose an active category."))

    @api.constrains("stage_ids", "company_id")
    def _check_pipeline_usage(self):
        # Existence-only elevation is necessary for shared configuration: a
        # manager must not invalidate records hidden by ownership/company rules.
        # Never return their names, IDs, counts or other business data.
        leads = self.env["crm.lead"].sudo().with_context(active_test=False)
        for category in self:
            invalid = Domain("stage_id", "not in", category.stage_ids.ids)
            if category.company_id:
                invalid |= Domain("company_id", "!=", category.company_id.id)
            if leads.search_count(
                Domain("pipeline_category_id", "=", category.id) & invalid,
                limit=1,
            ):
                raise ValidationError(_(
                    "This change would invalidate existing leads or opportunities, including archived records. "
                    "Keep their stage mappings and company scope, or explicitly reclassify the records first."
                ))

    @api.ondelete(at_uninstall=False)
    def _unlink_except_used(self):
        if self.env["crm.lead"].sudo().with_context(active_test=False).search_count(
            [("pipeline_category_id", "in", self.ids)], limit=1,
        ):
            raise UserError(_("This pipeline category is used by CRM records. Archive it instead of deleting it."))

    def action_open_pipeline(self):
        self.ensure_one()
        self.check_access("read")
        if not self.stage_ids:
            raise UserError(_("Configure at least one stage on this category before opening its pipeline."))
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_lead_action_pipeline")
        # The native action contains literal defaults, not executable rules.
        context = dict(self.env.context, **literal_eval(action.get("context") or "{}"))
        context.update({
            "pipeline_category_scope_id": self.id,
            "default_pipeline_category_id": self.id,
        })
        if self.company_id:
            context["default_company_id"] = self.company_id.id
        action.update({
            "name": _("Pipeline: %(category)s", category=self.display_name),
            "domain": list(
                Domain(literal_eval(action.get("domain") or "[]"))
                & Domain("pipeline_category_id", "=", self.id)
            ),
            "context": context,
        })
        # Do not reload the unscoped CRM action when restoring this dynamic action.
        action.pop("id", None)
        action.pop("path", None)
        return action

    def action_open_stage_reorder(self):
        self.ensure_one()
        self.check_access("read")
        if not self.stage_ids:
            raise UserError(_("Configure at least one stage before reordering this pipeline."))
        action = self.env["ir.actions.actions"]._for_xml_id("crm.crm_stage_action")
        action.update({
            "name": _("Reorder Stages: %(category)s", category=self.display_name),
            "domain": [("id", "in", self.stage_ids.ids)],
            "context": {"create": False},
            "views": [(self.env.ref("kpability_pipeline_categories.crm_stage_view_list_reorder").id, "list")],
            "view_mode": "list",
        })
        action.pop("id", None)
        action.pop("path", None)
        return action
