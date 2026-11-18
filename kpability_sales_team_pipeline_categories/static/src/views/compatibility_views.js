import { registry } from "@web/core/registry";
import { formView } from "@web/views/form/form_view";
import { listView } from "@web/views/list/list_view";

// Keep the report read-only without modifying native CRM controllers globally.
// edit="0" alone still leaves native Archive and bound mass actions available.
registry.category("views").add("pipeline_team_compatibility_list", {
    ...listView,
    props: (generic_props, view) => ({
        ...listView.props(generic_props, view),
        allowSelectors: false,
        info: { ...generic_props.info, actionMenus: null },
    }),
});

registry.category("views").add("pipeline_team_compatibility_form", {
    ...formView,
    props: (generic_props, view) => ({
        ...formView.props(generic_props, view),
        info: { ...generic_props.info, actionMenus: null },
    }),
});
