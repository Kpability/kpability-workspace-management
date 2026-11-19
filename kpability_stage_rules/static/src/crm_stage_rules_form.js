import "@crm/views/crm_form/crm_form";
import { _t } from "@web/core/l10n/translation";
import { evaluateBooleanExpr } from "@web/core/py_js/py";
import { registry } from "@web/core/registry";
import { TARGET_FIELDS, evaluateStageRules, hasFieldValue } from "./stage_rules";

const views = registry.category("views");
const crmForm = views.get("crm_form");
const targetFields = new Set(TARGET_FIELDS);
const stageKey = (companyId, stageId) => `${companyId}:${stageId}`;

function addRestriction(nativeModifier, fieldName, state) {
    if (nativeModifier === "True" || nativeModifier === "1") {
        return nativeModifier;
    }
    const restriction = `'${fieldName}' in kpability_stage_${state}`;
    return nativeModifier ? `(${nativeModifier}) or (${restriction})` : restriction;
}

class StageRulesArchParser extends crmForm.ArchParser {
    parse(xmlDoc, models, modelName) {
        // Compose static, code-owned modifiers into this CRM form only. Neither
        // field names supplied by configuration nor condition operands become code.
        const arch = xmlDoc.cloneNode(true);
        for (const node of arch.querySelectorAll("field[name], label[for]")) {
            if (node.parentElement.closest("field")) {
                continue;
            }
            const fieldName = node.getAttribute("name") || node.getAttribute("for");
            if (targetFields.has(fieldName)) {
                node.setAttribute(
                    "invisible",
                    addRestriction(node.getAttribute("invisible"), fieldName, "invisible")
                );
            }
        }
        const archInfo = super.parse(arch, models, modelName);
        for (const fieldInfo of Object.values(archInfo.fieldNodes)) {
            if (targetFields.has(fieldInfo.name)) {
                for (const modifier of ["readonly", "required"]) {
                    fieldInfo[modifier] = addRestriction(fieldInfo[modifier], fieldInfo.name, modifier);
                }
            }
        }
        return archInfo;
    }
}

class StageRulesRecord extends crmForm.Model.Record {
    getStageRules(stage = this.data.stage_id, company = this.data.company_id) {
        if (this.resModel !== "crm.lead" || this.data.type !== "opportunity") {
            return [];
        }
        return this.model.stageRules.get(stageKey(company?.id, stage?.id)) || [];
    }

    get hasPendingStageChange() {
        return (
            this._values.stage_id?.id !== this.data.stage_id?.id &&
            (this.getStageRules().length > 0 ||
                this.getStageRules(this._values.stage_id, this._values.company_id).length > 0)
        );
    }

    _setEvalContext() {
        super._setEvalContext();
        const states = evaluateStageRules(this.getStageRules(), this.data, this.activeFields);
        Object.assign(this.evalContext, states);
        Object.assign(this.evalContextWithVirtualIds, states);
    }

    _isReadonly(fieldName) {
        // The renderer already restricted what could be edited at the time. If a
        // subsequent draft change locks a field, keep that edit in the save payload
        // while still honoring Odoo's original write filtering.
        const readonly = this.activeFields[fieldName].readonly;
        if (!targetFields.has(fieldName) || !readonly) {
            return super._isReadonly(fieldName);
        }
        return evaluateBooleanExpr(readonly, {
            ...this.evalContextWithVirtualIds,
            kpability_stage_readonly: [],
        });
    }

    _isRequired(fieldName) {
        // An untouched existing record should still be able to use its native
        // actions (for example, open the Won Reasons wizard).
        const required = this.activeFields[fieldName].required;
        if (this.dirty || this.isNew || !targetFields.has(fieldName) || !required) {
            return super._isRequired(fieldName);
        }
        return evaluateBooleanExpr(required, {
            ...this.evalContextWithVirtualIds,
            kpability_stage_required: [],
        });
    }

    update(changes) {
        if (
            !this.isInEdition && Object.hasOwn(changes, "stage_id") &&
            changes.stage_id?.id !== this.data.stage_id?.id &&
            (this.getStageRules().length || this.getStageRules(
                changes.stage_id || false, changes.company_id ?? this.data.company_id
            ).length)
        ) {
            // Some read-only CRM views still offer a clickable statusbar that
            // saves immediately. Don't bypass the view's native editing policy.
            this.model.notification.add(
                _t("Open an editable opportunity form to change to or from this stage."),
                { type: "warning" }
            );
            return Promise.resolve();
        }
        return super.update(changes);
    }

    explainPendingStageChange() {
        this.model.notification.add(
            _t("Save or discard the stage change before continuing."),
            { type: "warning" }
        );
    }

    async _save({ stageRulesExplicitSave, ...options } = {}) {
        if (this.hasPendingStageChange && !stageRulesExplicitSave) {
            if (!this.model._urgentSave) {
                this.explainPendingStageChange();
            }
            return false;
        }
        if (this.dirty || this.isNew) {
            const { kpability_stage_required, kpability_stage_readonly } = this.evalContextWithVirtualIds;
            const blockedFields = kpability_stage_required.filter((name) =>
                !hasFieldValue(this.data[name]) &&
                (this._isInvisible(name) || this._isReadonly(name) || kpability_stage_readonly.includes(name))
            );
            if (blockedFields.length) {
                this.model.notification.add(
                    _t(
                        "This stage requires %(fields)s, but you cannot edit those fields here. Change the stage or ask your CRM manager to review the stage rules.",
                        { fields: blockedFields.map((name) => this.fields[name].string).join(", ") }
                    ),
                    { type: "danger", title: _t("Stage rule prevents saving") }
                );
                return false;
            }
        }
        return super._save(options);
    }
}

class StageRulesModel extends crmForm.Model {
    static Record = StageRulesRecord;

    setup() {
        super.setup(...arguments);
        this.stageRules = new Map();
        this.rulesByRecordData = new WeakMap();
    }

    async _loadData(config, cache) {
        const data = await super._loadData(config, cache);
        if (config.resModel !== "crm.lead" || data?.type !== "opportunity") {
            return data;
        }
        const rules = await this.orm.call("crm.lead", "get_stage_rules_for_form", [], {
            context: config.context,
        });
        const rulesByStage = new Map();
        for (const rule of rules) {
            const key = stageKey(rule.company_id, rule.stage_id);
            const stageRules = rulesByStage.get(key) || [];
            stageRules.push(rule);
            rulesByStage.set(key, stageRules);
        }
        this.rulesByRecordData.set(data, rulesByStage);
        return data;
    }

    _createRoot(config, data) {
        this.stageRules = this.rulesByRecordData.get(data) || new Map();
        return super._createRoot(config, data);
    }
}

class StageRulesController extends crmForm.Controller {
    saveButtonClicked(params = {}) {
        return super.saveButtonClicked({ ...params, stageRulesExplicitSave: true });
    }

    async beforeVisibilityChange() {
        if (!this.model.root?.hasPendingStageChange) {
            return super.beforeVisibilityChange(...arguments);
        }
    }
}

views.add("kpability_stage_rules_crm_form", {
    ...crmForm,
    ArchParser: StageRulesArchParser,
    Model: StageRulesModel,
    Controller: StageRulesController,
});
