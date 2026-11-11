import { useListener } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { CharField, charField } from "@web/views/fields/char/char_field";

export class ReasonCustomField extends CharField {
  setup() {
    super.setup();
    useListener(this.input, "input", (ev) => this.clearReason(ev.target.value));
  }

  // s_won_reason_custom -> won_reason_id
  get reasonFieldName() {
    return this.props.name.replace(/^s_/, "").replace(/_custom$/, "_id");
  }

  clearReason(value) {
    const { record } = this.props;
    if (value.trim() && record.data[this.reasonFieldName]) {
      record.update({ [this.reasonFieldName]: false });
    }
  }
}

registry.category("fields").add("reason_custom", {
  ...charField,
  component: ReasonCustomField,
});
