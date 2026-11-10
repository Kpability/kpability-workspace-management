import { signal } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { SelectionField } from "@web/views/fields/selection/selection_field";
import { ListRenderer } from "@web/views/list/list_renderer";
import { listView } from "@web/views/list/list_view";

class UserRolesRenderer extends ListRenderer {
  static template = "workspace_management.UserRolesRenderer";
  static recordRowTemplate = "workspace_management.UserRolesRow";

  static components = {
    ...ListRenderer.components,
    SelectionField,
  };

  setup() {
    super.setup();
    this.orm = useService("orm");
    this.notification = useService("notification");
    this.saving = signal(false);
  }

  get roleColumns() {
    return (
      this.props.list.model.config.context
        .workspace_role_columns || []
    );
  }

  getActiveColumns() {
    return [
      ...super.getActiveColumns(),
      ...this.roleColumns.map((role) => ({
        id: `workspace_role_${role.id}`,
        type: "workspace_role",
        name: "group_ids",
        role,
      })),
    ];
  }

  roleRecord(record, role) {
    const explicit = new Set(
      record.data.group_ids.currentIds
    );
    const effective = new Set(
      record.data.all_group_ids.currentIds
    );
    const ownIds = new Set(role.groups.map((group) => group.id));

    // Follow the native hierarchy order for the visible role.
    const selected = role.groups.findLast(
      (group) => effective.has(group.id)
    );

    // Roles implied by another privilege cannot be downgraded here.
    const floor = role.groups.findLastIndex((group) =>
      group.impliers.some(
        (id) => !ownIds.has(id) && explicit.has(id)
      )
    );

    const options = role.groups
      .slice(Math.max(floor, 0))
      .map((group) => [String(group.id), group.name]);

    if (floor < 0) {
      options.unshift(["none", role.emptyLabel]);
    }

    // SelectionField needs only fields, data and update for this type.
    return {
      fields: {
        role: {
          type: "selection",
          selection: options,
        },
      },
      data: {
        role: selected ? String(selected.id) : "none",
      },
      update: ({ role: value }) =>
        this.saveRole(record, role, value),
    };
  }

  async saveRole(record, role, value) {
    if (this.saving()) {
      return;
    }

    const selected = role.groups.find(
      (group) => String(group.id) === value
    );

    if (value !== "none" && !selected) {
      return;
    }

    const commands = role.groups.map(
      (group) => [3, group.id]
    );

    if (selected) {
      commands.push([4, selected.id]);
    }

    this.saving.set(true);

    try {
      await this.orm.write(
        "res.users",
        [record.resId],
        { group_ids: commands }
      );

      await record.load();
    } catch (error) {
      this.notification.add(
        error.data?.message ||
        error.message ||
        _t("Could not save the role."),
        { type: "danger" }
      );
    } finally {
      this.saving.set(false);
    }
  }


}

registry.category("views").add("workspace_user_roles", {
  ...listView,
  Renderer: UserRolesRenderer,
});