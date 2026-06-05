/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";
import { rpc } from "@web/core/network/rpc";

/**
 * Apple-style configurator widget.
 *
 * Responsibilities:
 *   - Real-time price recalculation when PTAV / optional product selection changes
 *   - Image cross-fade when colour swatch changes
 *   - Variant exclusion enforcement (server-rendered exclusion table)
 *   - Add-to-bag → /shop/cart/update_json (Odoo native)
 *   - Trigger cart drawer open on success
 */
publicWidget.registry.AppleConfigurator = publicWidget.Widget.extend({
    selector: ".apple-configurator",
    events: {
        "change input.ptav-input": "_onPtavChange",
        "change input.optional-input": "_onOptionalChange",
        "change input.optional-toggle-input": "_onSoftwareToggle",
        "change input.tradein-input": "_onTradeinToggle",
        "change input.laser-toggle-input": "_onLaserToggle",
        "input .laser-input": "_onLaserInput",
        "click .swatch": "_onSwatchClick",
        "click .add-to-bag": "_onAddToBag",
        "click .help-trigger": "_onHelpClick",
        "keydown .rc-card": "_onCardKeyDown",
    },

    start() {
        this._cacheDom();
        this._buildExclusionTable();
        this._bindRadioCardClick();
        this._refreshAvailability();
        this._recalcPrice(/* initial */ true);
        return this._super(...arguments);
    },

    _cacheDom() {
        this.$el = this.el;
        this.basePrice = parseFloat(this.el.dataset.basePrice) || 0;
        this.colorAttrId = parseInt(this.el.dataset.colorAttrId || 0);
        this.productTmplId = parseInt(this.el.dataset.productTmplId);
        this.currencySymbol = this.el.dataset.currencySymbol || "NT$";
        this._priceDisplays = this.el.querySelectorAll('[data-display="total"]');
        this._mainImage = this.el.querySelector(".main-image");
    },

    _buildExclusionTable() {
        try {
            const raw = this.el.dataset.exclusionTable || "{}";
            this._exclusionTable = JSON.parse(raw);
        } catch (e) {
            this._exclusionTable = {};
        }
    },

    /**
     * Whole .rc-card label is clickable — but if user clicks on the <input>
     * directly it bubbles up. Either way the input receives 'change'.
     * We also want clicking anywhere on the card to focus the input for a11y.
     */
    _bindRadioCardClick() {
        this.el.querySelectorAll(".rc-card").forEach((card) => {
            card.addEventListener("click", (ev) => {
                const input = card.querySelector("input");
                if (input && !input.disabled && ev.target !== input) {
                    input.checked = input.type === "checkbox" ? !input.checked : true;
                    input.dispatchEvent(new Event("change", { bubbles: true }));
                }
            });
        });
    },

    // ─── Price recalculation ─────────────────────────

    _recalcPrice(skipAnimation) {
        let total = this.basePrice;
        let extras = 0;

        // Sum selected PTAV price_extra
        this.el.querySelectorAll("input.ptav-input:checked").forEach((inp) => {
            extras += parseFloat(inp.dataset.priceExtra || 0);
        });

        // Sum selected optional products
        this.el.querySelectorAll("input.optional-input:checked").forEach((inp) => {
            extras += parseFloat(inp.dataset.price || 0);
        });

        total += extras;

        if (skipAnimation) {
            this._setPrice(total);
        } else {
            this._animatePriceUpdate(total);
        }
    },

    _setPrice(total) {
        const formatted = this._formatCurrency(total);
        this._priceDisplays.forEach((el) => {
            el.textContent = formatted;
        });
    },

    _animatePriceUpdate(total) {
        const formatted = this._formatCurrency(total);
        this._priceDisplays.forEach((el) => {
            el.classList.add("fade-out");
            setTimeout(() => {
                el.textContent = formatted;
                el.classList.remove("fade-out");
                el.classList.add("fade-in");
                setTimeout(() => el.classList.remove("fade-in"), 200);
            }, 150);
        });
    },

    _formatCurrency(amount) {
        // Format as TWD-style: NT$XX,XXX (no decimals)
        const rounded = Math.round(amount);
        return `${this.currencySymbol}${rounded.toLocaleString("en-US")}`;
    },

    // ─── Event handlers ──────────────────────────────

    _onPtavChange(ev) {
        const input = ev.currentTarget;
        const attrId = input.dataset.attributeId;
        this.el
            .querySelectorAll(`input.ptav-input[data-attribute-id="${attrId}"]`)
            .forEach((inp) => {
                const wrap = inp.closest(".form-selector") || inp.closest(".rc-card");
                if (wrap) wrap.classList.toggle("is-selected", inp.checked);
                if (wrap) wrap.classList.toggle("selected", inp.checked); // legacy
            });

        this._recalcPrice();
        this._refreshAvailability();

        if (this.colorAttrId && parseInt(input.dataset.attributeId) === this.colorAttrId) {
            const swatch = input.closest(".swatch");
            this._swapMainImage(swatch?.dataset.imageUrl);
            const colorLabel = this.el.querySelector(".active-color-name");
            if (colorLabel) colorLabel.textContent = input.dataset.displayName || "";
        }
    },

    _onOptionalChange(ev) {
        const wrap = ev.currentTarget.closest(".form-selector") ||
                     ev.currentTarget.closest(".rc-card");
        if (wrap) {
            wrap.classList.toggle("is-selected", ev.currentTarget.checked);
            wrap.classList.toggle("selected", ev.currentTarget.checked);
        }
        this._recalcPrice();
    },

    /**
     * Software toggle (FCP / Logic Pro): radio group within the same software_id.
     * Only the "yes please install" option contributes to price (its
     * input also has class `optional-input`); the "no thanks" option has 0.
     */
    _onSoftwareToggle(ev) {
        const input = ev.currentTarget;
        const groupName = input.name;
        this.el.querySelectorAll(`input[name="${groupName}"]`).forEach((r) => {
            const wrap = r.closest(".form-selector");
            if (wrap) wrap.classList.toggle("is-selected", r.checked);
        });
        this._recalcPrice();
    },

    /**
     * Trade-in radio: pure UI choice, no cart impact.
     * - Toggles .is-selected class on form-selector wrappers
     * - Expands/collapses .rf-tradeupinline-drawer when 加入換購 chosen
     */
    _onTradeinToggle(ev) {
        const input = ev.currentTarget;
        const groupName = input.name;
        this.el.querySelectorAll(`input[name="${groupName}"]`).forEach((r) => {
            const wrap = r.closest(".form-selector") || r.closest(".rc-card");
            if (wrap) wrap.classList.toggle("is-selected", r.checked);
        });
        const drawer = this.el.querySelector(".rf-tradeupinline-drawer");
        if (drawer) {
            const showDrawer = input.value === "join" && input.checked;
            if (showDrawer) {
                drawer.removeAttribute("hidden");
            } else {
                drawer.setAttribute("hidden", "hidden");
            }
        }
    },

    // ─── Laser Engraving ──────────────────────────
    _onLaserToggle(ev) {
        const input = ev.currentTarget;
        // update is-selected on all radio rows
        this.el.querySelectorAll('input[name="laser-engrave"]').forEach((r) => {
            const wrap = r.closest(".form-selector");
            if (wrap) wrap.classList.toggle("is-selected", r.checked);
        });
        const drawer = this.el.querySelector(".as-laser-drawer");
        if (!drawer) return;
        const show = input.value === "1" && input.checked;
        if (show) {
            drawer.removeAttribute("hidden");
            this._syncLaserPreviewColor();
            // focus first input
            const first = drawer.querySelector(".laser-input");
            if (first) first.focus();
        } else {
            drawer.setAttribute("hidden", "hidden");
            // clear inputs & preview when dismissed
            drawer.querySelectorAll(".laser-input").forEach((i) => { i.value = ""; });
            this._updateLaserPreview();
        }
    },

    _onLaserInput(ev) {
        const input = ev.currentTarget;
        // update character counter
        const field = input.closest(".as-laser-field");
        if (field) {
            const counter = field.querySelector(".as-laser-count");
            if (counter) counter.textContent = [...input.value].length;
        }
        this._updateLaserPreview();
    },

    _updateLaserPreview() {
        const line1Input = this.el.querySelector("#laser-line1");
        const prev1 = this.el.querySelector(".as-laser-preview-line1");
        if (!prev1) return;
        const text1 = line1Input ? line1Input.value.trim() : "";
        prev1.textContent = text1;
    },

    _syncLaserPreviewColor() {
        const device = this.el.querySelector(".as-laser-preview-device");
        if (!device) return;
        // Find the active swatch's background-color
        const activeSwatch = this.el.querySelector(".swatch[aria-checked='true']");
        if (activeSwatch) {
            const bg = activeSwatch.style.backgroundColor;
            if (bg) {
                device.style.background = `radial-gradient(ellipse at 30% 30%, color-mix(in srgb, ${bg} 80%, #fff), color-mix(in srgb, ${bg} 50%, #fff))`;
                return;
            }
        }
        // fallback: light silver
        device.style.background = "";
    },

    _onSwatchClick(ev) {
        const swatch = ev.currentTarget;
        // Toggle aria-checked among siblings
        swatch.parentElement.querySelectorAll(".swatch").forEach((s) => {
            s.setAttribute("aria-checked", "false");
        });
        swatch.setAttribute("aria-checked", "true");
        this._syncLaserPreviewColor();

        // Find the matching ptav input and check it (this triggers price + image)
        const ptavId = swatch.dataset.ptavId;
        const input = this.el.querySelector(`input.ptav-input[data-ptav-id="${ptavId}"]`);
        if (input) {
            input.checked = true;
            input.dispatchEvent(new Event("change", { bubbles: true }));
        } else {
            // No PTAV input (color attribute might be on left only) — just swap image
            this._swapMainImage(swatch.dataset.imageUrl);
            const colorLabel = this.el.querySelector(".active-color-name");
            if (colorLabel) colorLabel.textContent = swatch.getAttribute("aria-label") || "";
        }
    },

    _swapMainImage(newSrc) {
        if (!this._mainImage || !newSrc) return;
        this._mainImage.classList.add("cross-fade-out");
        setTimeout(() => {
            this._mainImage.src = newSrc;
            this._mainImage.onload = () =>
                this._mainImage.classList.remove("cross-fade-out");
        }, 200);
    },

    _onCardKeyDown(ev) {
        // Arrow keys navigate within fieldset
        if (!["ArrowUp", "ArrowDown", "ArrowLeft", "ArrowRight"].includes(ev.key))
            return;
        ev.preventDefault();
        const fieldset = ev.currentTarget.closest(".rc-dimension");
        if (!fieldset) return;
        const cards = Array.from(fieldset.querySelectorAll(".rc-card"));
        const idx = cards.indexOf(ev.currentTarget);
        const dir = ev.key === "ArrowUp" || ev.key === "ArrowLeft" ? -1 : 1;
        const next = cards[(idx + dir + cards.length) % cards.length];
        if (next) {
            next.focus();
            const input = next.querySelector("input");
            if (input && !input.disabled && input.type === "radio") {
                input.checked = true;
                input.dispatchEvent(new Event("change", { bubbles: true }));
            }
        }
    },

    _onHelpClick(ev) {
        ev.preventDefault();
        // Placeholder: in real impl we'd open a popover with apple_help_text
        console.log("Help requested for", ev.currentTarget.closest(".rc-dimension"));
    },

    // ─── Variant exclusion enforcement ───────────────

    _refreshAvailability() {
        const chosen = Array.from(
            this.el.querySelectorAll("input.ptav-input:checked")
        ).map((i) => parseInt(i.dataset.ptavId));

        this.el.querySelectorAll("input.ptav-input").forEach((inp) => {
            const id = parseInt(inp.dataset.ptavId);
            const exclusions = this._exclusionTable[id] || [];
            const isExcluded = exclusions.some((ex) => chosen.includes(ex));
            inp.disabled = isExcluded && !inp.checked;
            const card = inp.closest(".rc-card");
            if (card) card.classList.toggle("disabled", inp.disabled);
        });
    },

    // ─── Add to bag ──────────────────────────────────

    async _onAddToBag(ev) {
        ev.preventDefault();
        const btn = ev.currentTarget;
        if (btn.disabled) return;
        btn.disabled = true;
        btn.classList.add("loading");

        try {
            const ptavIds = Array.from(
                this.el.querySelectorAll("input.ptav-input:checked")
            ).map((i) => parseInt(i.dataset.ptavId));

            const optionalIds = Array.from(
                this.el.querySelectorAll("input.optional-input:checked")
            ).map((i) => parseInt(i.dataset.productId));

            // Custom endpoint: server resolves dynamic variant from PTAV combo
            // and folds optional products into same sale.order
            const res = await rpc("/shop/buy-mac/cart/add", {
                product_template_id: this.productTmplId,
                product_template_attribute_value_ids: ptavIds,
                optional_product_ids: optionalIds,
            });

            if (res && res.error) {
                throw new Error(res.error);
            }

            this._showToast("已加入購物袋");
            this._openCartDrawer();
            window.dispatchEvent(
                new CustomEvent("apple-cart-updated", { detail: res })
            );
        } catch (e) {
            this._showToast(e.message || "加入失敗，請稍後再試", true);
        } finally {
            btn.disabled = false;
            btn.classList.remove("loading");
        }
    },

    _openCartDrawer() {
        const drawer = this.el.querySelector(".cart-drawer");
        const backdrop = this.el.querySelector(".drawer-backdrop");
        if (!drawer) return;
        drawer.removeAttribute("hidden");
        backdrop?.removeAttribute("hidden");
        // Force reflow before adding .open
        drawer.offsetHeight;
        drawer.classList.add("open");
        backdrop?.classList.add("open");
        // a11y: focus the close button when drawer opens
        const closeBtn = drawer.querySelector(".drawer-close");
        if (closeBtn) {
            setTimeout(() => closeBtn.focus(), 100);
        }
    },

    _showToast(message, isError) {
        const toast = document.createElement("div");
        toast.className = "apple-toast" + (isError ? " error" : "");
        toast.textContent = message;
        toast.setAttribute("role", "alert");
        this.el.appendChild(toast);
        toast.offsetHeight;
        toast.classList.add("show");
        setTimeout(() => {
            toast.classList.remove("show");
            setTimeout(() => toast.remove(), 300);
        }, 2000);
    },
});
