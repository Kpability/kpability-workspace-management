import { Component, onWillStart, t, useProps } from "@odoo/owl";
import { DomainSelector, domainSelectorProps } from "@web/core/domain_selector/domain_selector";
import { getDomainDisplayedOperators } from "@web/core/domain_selector/domain_selector_operator_editor";
import { ModelFieldSelector } from "@web/core/model_field_selector/model_field_selector";
import { registry } from "@web/core/registry";
import { condition } from "@web/core/tree_editor/condition_tree";
import { getOperatorEditorInfo } from "@web/core/tree_editor/tree_editor_operator_editor";
import { getDefaultValue } from "@web/core/tree_editor/tree_editor_value_editors";
import { getDefaultPath } from "@web/core/tree_editor/utils";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { canTarget } from "./stage_rules";

class StageRulesFieldPicker extends Component {
    static template = "kpability_stage_rules.FieldPicker";
    static components = { ModelFieldSelector };
    props = useProps(standardFieldProps);

    setup() {
        const orm = useService("orm");
        onWillStart(async () => {
            const fields = await orm.call("stage.rules.field", "get_field_choices", []);
            this.choices = new Set(fields);
        });
    }

    filter(field) {
        return this.choices.has(field.name) && canTarget(field.name, field.type);
    }

    update(name) {
        return this.props.record.update({ [this.props.name]: name });
    }
}

function getOperators(fieldDef) {
    const operators = getDomainDisplayedOperators(fieldDef);
    if (["many2one", "many2many"].includes(fieldDef?.type)) {
        return operators.filter((operator) => !["ilike", "not ilike"].includes(operator));
    }
    if (["date", "datetime"].includes(fieldDef?.type)) {
        return operators.filter((operator) => operator !== "in range");
    }
    if (["char", "text"].includes(fieldDef?.type)) {
        // The browser domain matcher does not anchor the native "starts with" operator.
        return operators.filter((operator) => operator !== "starts with");
    }
    return operators;
}

class StageRulesDomainSelector extends DomainSelector {
    props = useProps({ ...domainSelectorProps, choices: t.array(t.string()) });

    getShowArchivedCheckBox() {
        return false;
    }

    getDefaultCondition(fieldDefs) {
        const choices = this.props.choices;
        const available = Object.fromEntries(
            Object.entries(fieldDefs).filter(([name]) => choices.includes(name))
        );
        const name = getDefaultPath(available);
        const fieldDef = available[name];
        const operator = this.getDefaultOperator(fieldDef);
        return condition(name, operator, getDefaultValue(fieldDef, operator));
    }

    getDefaultOperator(fieldDef) {
        return getOperators(fieldDef)[0];
    }

    getOperatorEditorInfo(fieldDef) {
        return getOperatorEditorInfo(getOperators(fieldDef), fieldDef);
    }

    getPathEditorInfo(...args) {
        const info = super.getPathEditorInfo(...args);
        const names = this.props.choices;
        return {
            ...info,
            extractProps: (params) => ({
                ...info.extractProps(params),
                filter: (field) => names.includes(field.name),
                followRelation: false,
            }),
        };
    }
}

class StageRulesCondition extends Component {
    static template = "kpability_stage_rules.Condition";
    static components = { StageRulesDomainSelector };
    props = useProps({ ...standardFieldProps, allowTargets: t.boolean() });

    get choices() {
        const key = this.props.allowTargets ? "all" : "non_targets";
        return this.props.record.data.j_condition_fields?.[key] || [];
    }

    update(domain) {
        return this.props.record.update({ [this.props.name]: domain });
    }
}

const fields = registry.category("fields");
fields.add("kpability_stage_field_picker", {
    component: StageRulesFieldPicker,
    supportedTypes: ["char"],
});
fields.add("kpability_stage_condition", {
    component: StageRulesCondition,
    supportedTypes: ["text"],
    extractProps: ({ options }) => ({ allowTargets: Boolean(options.allow_targets) }),
});
