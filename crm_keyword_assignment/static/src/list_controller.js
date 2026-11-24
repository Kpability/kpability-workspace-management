import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { listView } from "@web/views/list/list_view";
import { ListController } from "@web/views/list/list_controller";
import { FormViewDialog } from "@web/views/view_dialogs/form_view_dialog";

export class CrmKeywordAssignmentListController extends ListController {
    setup() {
        super.setup();
        this.dialog = useService("dialog");
    }

    async createRecord() {
        this.dialog.add(FormViewDialog, {
            resModel: this.props.resModel,
            context: this.props.context,
            title: _t("Keyword Rule"),
            onRecordSaved: async () => {
                await this.model.root.load();
            },
        });
    }
}

registry.category("views").add("crm_keyword_assignment_list", {
    ...listView,
    Controller: CrmKeywordAssignmentListController,
});
