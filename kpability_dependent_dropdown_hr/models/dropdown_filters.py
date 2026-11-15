from odoo import api, fields, models
from odoo.exceptions import AccessError, ValidationError
from odoo.fields import Domain


class DropdownFilters(models.Model):
    _inherit = "dropdown.filters"

    department_id = fields.Many2one(
        "hr.department", string="Eligible Department", check_company=True, ondelete="restrict",
        domain="[('company_id', '=', company_id)]",
        help="Exact department, not its descendants. No name matching or automatic Sales mapping.",
    )
    s_binding_key = fields.Char(related="adapter_id.s_key")

    @api.constrains("department_id", "company_id", "adapter_id", "active")
    def _check_department(self):
        for rule in self:
            is_department = rule.adapter_id.s_key in (
                "crm_sales_department", "contacts_sales_department",
            )
            if is_department and rule.active and not rule.department_id:
                raise ValidationError(self.env._("Select a department before activating this filter."))
            if rule.department_id and rule.department_id.company_id != rule.company_id:
                raise ValidationError(self.env._("The department must belong to the filter's company."))
            if rule.department_id and not is_department:
                raise ValidationError(self.env._("A department applies only to a salesperson binding."))

    def _domain_for_rule(self, record):
        self.ensure_one()
        if self.adapter_id.s_key not in ("crm_sales_department", "contacts_sales_department"):
            return super()._domain_for_rule(record)
        if not self.department_id:
            return Domain.FALSE
        try:
            self.department_id.check_access("read")
            self.env["hr.employee.public"].check_access("read")
        except AccessError:
            return Domain.FALSE
        return Domain.AND([
            [("active", "=", True), ("share", "=", False)],
            [("company_ids", "in", self.company_id.ids)],
            [("employee_public_ids", "any", [
                ("company_id", "=", self.company_id.id),
                ("department_id", "=", self.department_id.id),
                ("active", "=", True),
            ])],
        ])
