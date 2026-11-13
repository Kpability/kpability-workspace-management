/** @odoo-module **/

(() => {
    "use strict";

    async function loadCategories(container) {
        if (container.dataset.kpLoaded) {
            return;
        }
        container.dataset.kpLoaded = "1";
        let categories = [];
        try {
            const response = await fetch(container.dataset.kpEndpoint, {
                method: "GET",
                credentials: "same-origin",
                headers: {"Accept": "application/json"},
            });
            if (response.ok) {
                categories = await response.json();
            }
        } catch {
            categories = [];
        }
        container.replaceChildren();
        if (!categories.length) {
            const empty = document.createElement("span");
            empty.className = "text-muted small";
            empty.textContent = "No pipeline is available right now.";
            container.appendChild(empty);
            return;
        }
        for (const category of categories) {
            const wrapper = document.createElement("div");
            wrapper.className = "form-check";
            const input = document.createElement("input");
            input.type = "checkbox";
            input.className = "form-check-input";
            input.name = `kp_pipeline_category_id_${category.id}`;
            input.value = String(category.id);
            input.id = `kp_pipeline_category_${category.id}`;
            const label = document.createElement("label");
            label.className = "form-check-label";
            label.htmlFor = input.id;
            label.textContent = category.name;
            if (category.description) {
                const description = document.createElement("span");
                description.className = "text-muted small d-block";
                description.textContent = category.description;
                label.appendChild(description);
            }
            wrapper.append(input, label);
            container.appendChild(wrapper);
        }
    }

    function init() {
        for (const container of document.querySelectorAll("[data-kp-pipeline-categories]")) {
            loadCategories(container);
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", init);
    } else {
        init();
    }
})();
