/** @odoo-module **/

// Upgrade guard for forms previously copied into editable website pages.
// There is no category fetch, selector creation, or submission integration.
(() => {
    "use strict";

    function retireForms() {
        for (const container of document.querySelectorAll("[data-kp-pipeline-categories]")) {
            const form = container.closest("form");
            container.textContent = "Website pipeline intake is unavailable. Please contact us directly.";
            if (!form) {
                continue;
            }
            form.addEventListener("submit", (event) => event.preventDefault(), true);
            for (const input of form.querySelectorAll("input, textarea, select, button")) {
                input.disabled = true;
            }
            for (const button of form.querySelectorAll(".s_website_form_send")) {
                button.classList.remove("s_website_form_send");
                button.setAttribute("aria-disabled", "true");
                button.addEventListener("click", (event) => event.preventDefault(), true);
            }
        }
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", retireForms);
    } else {
        retireForms();
    }
})();
