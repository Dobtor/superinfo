/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

/**
 * Cart drawer — slide-in from right.
 *
 * Behaviour:
 *   - Listens for `apple-cart-updated` event after add-to-bag
 *   - Fetches current cart state via /shop/cart/update_json (qty=0 query trick)
 *   - Renders order_line summary with PTAV expansion
 *   - ESC key + click-backdrop closes drawer
 *   - Focus trap inside drawer when open
 */
publicWidget.registry.AppleCartDrawer = publicWidget.Widget.extend({
    selector: ".apple-configurator",
    events: {
        "click .drawer-close": "_close",
        "click .drawer-backdrop": "_close",
    },

    start() {
        this.drawer = this.el.querySelector(".cart-drawer");
        this.backdrop = this.el.querySelector(".drawer-backdrop");
        if (!this.drawer) return this._super(...arguments);

        this._onCartUpdated = this._onCartUpdated.bind(this);
        this._onKeyDown = this._onKeyDown.bind(this);
        this._onFocusTrap = this._onFocusTrap.bind(this);
        window.addEventListener("apple-cart-updated", this._onCartUpdated);
        document.addEventListener("keydown", this._onKeyDown);
        this.drawer.addEventListener("keydown", this._onFocusTrap);

        return this._super(...arguments);
    },

    _onFocusTrap(ev) {
        // Trap Tab/Shift+Tab focus inside drawer when open
        if (!this.drawer.classList.contains("open") || ev.key !== "Tab") return;
        const focusables = this.drawer.querySelectorAll(
            'button, [href], input, [tabindex]:not([tabindex="-1"])'
        );
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        if (ev.shiftKey && document.activeElement === first) {
            ev.preventDefault();
            last.focus();
        } else if (!ev.shiftKey && document.activeElement === last) {
            ev.preventDefault();
            first.focus();
        }
    },

    destroy() {
        window.removeEventListener("apple-cart-updated", this._onCartUpdated);
        document.removeEventListener("keydown", this._onKeyDown);
        this.drawer?.removeEventListener("keydown", this._onFocusTrap);
        this._super(...arguments);
    },

    _onCartUpdated(ev) {
        // Use the cart info passed from the configurator's add-to-bag rpc
        // (delivered via CustomEvent.detail). Avoids re-fetching cart state
        // — Odoo doesn't provide a JSON cart-read endpoint and we don't need
        // line-level detail here.
        this._renderBody(ev?.detail || {});
    },

    _onKeyDown(ev) {
        if (ev.key === "Escape" && this.drawer && this.drawer.classList.contains("open")) {
            this._close();
        }
    },

    _renderBody(cartData) {
        const body = this.drawer.querySelector(".drawer-body");
        if (!body) return;
        if (!cartData || !cartData.cart_quantity) {
            body.innerHTML = '<p class="drawer-empty">購物袋目前是空的。</p>';
            return;
        }
        const escape = (s) =>
            String(s).replace(/[&<>"']/g, (c) => ({
                "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;",
            }[c]));
        body.innerHTML = `
            <p class="drawer-status">
                <strong>${escape(cartData.product_name || "")}</strong> 已加入購物袋。
            </p>
            <p class="drawer-status">
                目前購物袋有 <strong>${cartData.cart_quantity}</strong> 件商品。
            </p>
        `;
    },

    _close() {
        if (!this.drawer) return;
        this.drawer.classList.remove("open");
        this.backdrop?.classList.remove("open");
        setTimeout(() => {
            this.drawer.setAttribute("hidden", "hidden");
            this.backdrop?.setAttribute("hidden", "hidden");
        }, 400);
    },
});
