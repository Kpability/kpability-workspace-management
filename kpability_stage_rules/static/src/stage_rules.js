import { serializeDate } from "@web/core/l10n/dates";

export const TARGET_FIELDS = [
    "date_deadline", "user_id", "campaign_id", "medium_id", "source_id", "referred",
];

export function hasFieldValue(value) {
    return value !== false && value != null && (typeof value !== "string" || value.trim() !== "");
}

function matchesCondition(condition, data) {
    if (!condition || !Object.hasOwn(data, condition.field_name)) {
        return false;
    }
    let value = data[condition.field_name];
    const isSet = hasFieldValue(value);
    if (condition.operator === "is_set") {
        return isSet;
    }
    if (condition.operator === "is_not_set") {
        return !isSet;
    }
    if (!isSet) {
        return false;
    }
    if (condition.field_name === "date_deadline") {
        value = serializeDate(value);
    } else if (typeof value === "string") {
        value = value.trim();
    }
    switch (condition.operator) {
        case "equals":
            return value === condition.value;
        case "not_equals":
            return value !== condition.value;
        case "before":
            return value < condition.value;
        case "after":
            return value > condition.value;
        default:
            return false;
    }
}

export function evaluateStageRules(rules, data, activeFields) {
    const invisible = new Set();
    const readonly = new Set();
    const required = new Set();
    for (const rule of rules) {
        const name = rule.field_name;
        if (
            !Object.hasOwn(activeFields, name) ||
            (rule.condition && !Object.hasOwn(activeFields, rule.condition.field_name))
        ) {
            continue;
        }
        const matches = matchesCondition(rule.condition, data);
        if (rule.visibility === "hidden" || (rule.visibility === "when" && !matches)) {
            invisible.add(name);
        }
        if (rule.enabled === "disabled" || (rule.enabled === "when" && !matches)) {
            readonly.add(name);
        }
        if (rule.required === "always" || (rule.required === "when" && matches)) {
            required.add(name);
        }
    }
    return {
        kpability_stage_invisible: [...invisible],
        kpability_stage_readonly: [...readonly],
        kpability_stage_required: [...required],
    };
}
