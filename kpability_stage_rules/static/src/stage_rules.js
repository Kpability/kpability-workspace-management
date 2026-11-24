import { Domain } from "@web/core/domain";

const supportedTypes = new Set([
    "boolean", "char", "date", "datetime", "float", "integer", "many2many",
    "many2one", "monetary", "selection", "text",
]);
const scopeFields = new Set(["company_id", "id", "stage_id", "type"]);

export function canTarget(name, type) {
    return !scopeFields.has(name) && supportedTypes.has(type);
}

export function hasRequiredValue(value, type) {
    if (["boolean", "float", "integer", "monetary"].includes(type)) {
        return true; // Odoo provides a value (including false or zero) for these types.
    }
    return type === "many2many" ? Boolean(value?.count) : Boolean(value);
}

function evaluateBehavior(behavior, context, activeFields, fields) {
    if (!behavior) {
        return undefined;
    }
    if (behavior.mode !== "when") {
        return true;
    }
    const values = {};
    for (const term of behavior.domain) {
        if (!Array.isArray(term)) {
            continue;
        }
        const [name] = term;
        if (!Object.hasOwn(activeFields, name) || !Object.hasOwn(context, name)) {
            // Don't treat a field excluded from this view as an empty value.
            return undefined;
        }
        const value = context[name];
        const type = fields[name].type;
        values[name] =
            type === "many2many" && !value?.length ? false :
            ["char", "text"].includes(type) && typeof value === "string" ? value.trim() || false :
            value ?? false;
    }
    return new Domain(behavior.domain).contains(values);
}

export function evaluateStageRules(rules, context, activeFields, fields) {
    const invisible = new Set();
    const readonly = new Set();
    const required = new Set();
    for (const { field_names, behaviors } of rules) {
        const visible = evaluateBehavior(behaviors.visibility, context, activeFields, fields);
        const editable = evaluateBehavior(behaviors.enabled, context, activeFields, fields);
        const mandatory = evaluateBehavior(behaviors.required, context, activeFields, fields);
        for (const name of field_names) {
            if (!Object.hasOwn(activeFields, name) || !canTarget(name, fields[name].type)) {
                continue;
            }
            if (visible !== undefined && (behaviors.visibility.mode === "hidden" || !visible)) {
                invisible.add(name);
            }
            if (editable !== undefined && (behaviors.enabled.mode === "disabled" || !editable)) {
                readonly.add(name);
            }
            if (mandatory) {
                required.add(name);
            }
        }
    }
    return {
        kpability_stage_invisible: [...invisible],
        kpability_stage_readonly: [...readonly],
        kpability_stage_required: [...required],
    };
}
