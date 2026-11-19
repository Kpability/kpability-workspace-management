import { Component, onWillStart, proxy, useProps } from "@odoo/owl";
import { CheckBox } from "@web/core/checkbox/checkbox";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_plugin";

class Menu extends Component {
    static template = "menu_management.Menu";
    static components = { Layout, CheckBox };
    props = useProps(standardActionServiceProps);

    setup() {
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = proxy({ roles: [], menus: [], saving: false });
        onWillStart(async () => {
            Object.assign(this.state, await this.orm.call("ir.ui.menu", "workspace_menu_data"));
        });
    }

    checked(role, menu) {
        return !menu.workspace_hidden_group_ids.includes(role.id) && (
            !menu.group_ids.length || menu.group_ids.some((id) => role.all_implied_ids.includes(id))
        );
    }

    icon(menu) {
        const parts = (menu.web_icon || "").split(",");
        return parts.length === 2 ? `/${parts.join("/")}` : "/web/static/img/default_icon_app.png";
    }

    async save(role, menus, enabled) {
        if (this.state.saving) {
            return;
        }
        this.state.saving = true;
        try {
            const updated = await this.orm.call("ir.ui.menu", "workspace_set_menu_group", [
                menus.map((menu) => menu.id), role.id, enabled,
            ]);
            for (const values of updated) {
                Object.assign(this.state.menus.find((menu) => menu.id === values.id), values);
            }
        } catch (error) {
            this.notification.add(error.data?.message || error.message, { type: "danger" });
        } finally {
            this.state.saving = false;
        }
    }
}

registry.category("actions").add("menu_management.Menu", Menu);
