/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.AppleContactUs = publicWidget.Widget.extend({
    selector: ".apple-contactus",
    events: {
        "click .ac-chip": "_onChipClick",
        "submit .ac-form": "_onFormSubmit",
    },

    start() {
        this._hiddenInput = this.el.querySelector("#ac_inquiry_type");
        return this._super(...arguments);
    },

    // ─── Inquiry type chips ───────────────────
    _onChipClick(ev) {
        const clicked = ev.currentTarget;
        this.el.querySelectorAll(".ac-chip").forEach(c => c.classList.remove("active"));
        clicked.classList.add("active");
        if (this._hiddenInput) {
            this._hiddenInput.value = clicked.dataset.value || clicked.textContent.trim();
        }
    },

    // ─── Form submit: loading state ───────────
    _onFormSubmit(ev) {
        const form = ev.currentTarget;
        const btn = form.querySelector(".ac-submit");
        if (!btn) return;
        btn.disabled = true;
        btn.innerHTML = `
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2"
                 style="animation: spin 0.8s linear infinite">
                <circle cx="12" cy="12" r="10" stroke-opacity="0.25"/>
                <path d="M12 2a10 10 0 0110 10" stroke-opacity="1"/>
            </svg>
            <span>傳送中…</span>`;

        // Inject spin keyframe once
        if (!document.getElementById("ac-spin-style")) {
            const s = document.createElement("style");
            s.id = "ac-spin-style";
            s.textContent = "@keyframes spin { to { transform: rotate(360deg); } }";
            document.head.appendChild(s);
        }
    },
});
